"""Расшифровка голосовых через OpenAI-совместимый endpoint (Whisper и аналоги). Один запрос на одно голосовое."""
import httpx

from .config import get_settings


class TranscribeError(RuntimeError):
    pass


def enabled() -> bool:
    s = get_settings()
    return bool(s.transcribe_api_url and s.transcribe_api_key)


async def transcribe(audio: bytes, filename: str = "voice.ogg", language: str = "ru") -> str:
    s = get_settings()
    if not enabled():
        raise TranscribeError("расшифровка не настроена")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(s.transcribe_api_url, headers={"Authorization": f"Bearer {s.transcribe_api_key}"},
                         data={"model": s.transcribe_model, "language": language}, files={"file": (filename, audio, "audio/ogg")})
    if r.status_code != 200:
        raise TranscribeError(f"сервис ответил {r.status_code}")
    return (r.json().get("text") or "").strip()
