import asyncio
import time

import pytest

from app import transcribe
from app.config import get_settings


@pytest.fixture
def local(monkeypatch):
    monkeypatch.setattr(get_settings(), "transcribe_engine", "local")
    monkeypatch.setattr(transcribe, "_local_available", lambda: True)
    calls = {"running": 0, "max": 0}

    def fake(audio, language):
        calls["running"] += 1
        calls["max"] = max(calls["max"], calls["running"])
        time.sleep(0.05)
        calls["running"] -= 1
        return f"текст {len(audio)}"

    monkeypatch.setattr(transcribe, "_local_transcribe", fake)
    return calls


async def test_local_runs_one_at_a_time(local):
    res = await asyncio.gather(*(transcribe.transcribe(b"x" * n) for n in (1, 2, 3)))
    assert res == ["текст 1", "текст 2", "текст 3"]
    assert local["max"] == 1  # сервер занят только одной расшифровкой
    assert transcribe.queue_size() == 0


async def test_queue_size_visible(local):
    t = [asyncio.create_task(transcribe.transcribe(b"a")) for _ in range(3)]
    await asyncio.sleep(0.01)
    assert transcribe.queue_size() == 3
    await asyncio.gather(*t)


async def test_error_wrapped(monkeypatch, local):
    def boom(audio, language):
        raise RuntimeError("bad file")

    monkeypatch.setattr(transcribe, "_local_transcribe", boom)
    with pytest.raises(transcribe.TranscribeError):
        await transcribe.transcribe(b"x")


def test_unload_after_idle(monkeypatch):
    monkeypatch.setattr(transcribe, "_model", object())
    monkeypatch.setattr(transcribe, "_last_used", time.monotonic() - 3600)
    assert transcribe.unload_if_idle() is True and transcribe._model is None


def test_off_engine(monkeypatch):
    monkeypatch.setattr(get_settings(), "transcribe_engine", "off")
    assert transcribe.enabled() is False


@pytest.mark.skipif(not transcribe._local_available(), reason="faster-whisper не установлен")
def test_real_model_smoke():
    """Короткая проверка, что настоящая модель грузится и не падает на тишине."""
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000)
    from faster_whisper import WhisperModel

    m = WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=1)
    segs, info = m.transcribe(io.BytesIO(buf.getvalue()), language="ru", vad_filter=True)
    assert isinstance(" ".join(s.text for s in segs), str) and info.duration == pytest.approx(1.0, abs=0.1)
