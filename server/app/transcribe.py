"""Расшифровка голосовых.

local: модель Whisper (faster-whisper) прямо на сервере, без ключей. Нагрузка ограничена:
одна расшифровка за раз (остальные ждут в очереди), не больше WHISPER_THREADS ядер,
модель выгружается из памяти после простоя. На 2 ядрах модель small тратит ~13 с на минуту речи.
api: внешний OpenAI-совместимый сервис.
"""
import asyncio
import io
import logging
import time

import httpx

from .config import get_settings

log = logging.getLogger(__name__)


class TranscribeError(RuntimeError):
    pass


_lock: asyncio.Lock | None = None
_lock_loop = None
_waiting = 0
_model = None
_last_used = 0.0


def _local_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def enabled() -> bool:
    s = get_settings()
    if s.transcribe_engine == "local":
        return _local_available()
    if s.transcribe_engine == "api":
        return bool(s.transcribe_api_url and s.transcribe_api_key)
    return False


def _get_lock() -> asyncio.Lock:
    """Замок создаётся в текущем цикле событий (в боте он один, в тестах у каждого теста свой)."""
    global _lock, _lock_loop
    loop = asyncio.get_running_loop()
    if _lock is None or _lock_loop is not loop:
        _lock, _lock_loop = asyncio.Lock(), loop
    return _lock


def queue_size() -> int:
    """Сколько голосовых ждут перед новым (включая то, что расшифровывается сейчас)."""
    return _waiting


def _load_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        s = get_settings()
        log.info("загружаю Whisper %s", s.whisper_model)
        _model = WhisperModel(s.whisper_model, device="cpu", compute_type="int8", cpu_threads=s.whisper_threads)
    return _model


def _local_transcribe(audio: bytes, language: str) -> str:
    model = _load_model()
    segments, _ = model.transcribe(io.BytesIO(audio), language=language, beam_size=1, vad_filter=True)
    return " ".join(s.text.strip() for s in segments).strip()


def unload_if_idle() -> bool:
    """Освобождает память, если модель давно не использовалась. Вызывается периодически из бота."""
    global _model
    idle = get_settings().whisper_idle_unload_min * 60
    if _model is not None and not (_lock and _lock.locked()) and time.monotonic() - _last_used > idle:
        _model = None
        log.info("Whisper выгружен из памяти после простоя")
        return True
    return False


async def _api_transcribe(audio: bytes, filename: str, language: str) -> str:
    s = get_settings()
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(s.transcribe_api_url, headers={"Authorization": f"Bearer {s.transcribe_api_key}"},
                         data={"model": s.transcribe_model, "language": language}, files={"file": (filename, audio, "audio/ogg")})
    if r.status_code != 200:
        raise TranscribeError(f"сервис ответил {r.status_code}")
    return (r.json().get("text") or "").strip()


async def transcribe(audio: bytes, filename: str = "voice.ogg", language: str = "ru") -> str:
    global _waiting, _last_used
    if not enabled():
        raise TranscribeError("расшифровка не настроена")
    if get_settings().transcribe_engine == "api":
        return await _api_transcribe(audio, filename, language)
    _waiting += 1
    try:
        async with _get_lock():  # строго по одному, чтобы не занять весь сервер
            try:
                return await asyncio.to_thread(_local_transcribe, audio, language)
            except Exception as e:  # битый файл, нехватка памяти и т.п.
                log.exception("ошибка расшифровки")
                raise TranscribeError("не удалось расшифровать") from e
            finally:
                _last_used = time.monotonic()
    finally:
        _waiting -= 1
