import io

from aiogram import Bot, F, Router
from aiogram.types import Message
from sqlalchemy import select

from app import transcribe
from app.config import get_settings
from app.db import SessionLocal
from app.models import User, VoiceNote

router = Router()


@router.message(F.voice | F.audio | F.video_note)
async def voice(message: Message, bot: Bot) -> None:
    media = message.voice or message.audio or message.video_note
    duration = getattr(media, "duration", 0) or 0
    limit = get_settings().voice_max_sec
    if not transcribe.enabled():
        await message.answer("Голосовое получил, но расшифровка пока не включена. Можно написать текстом или надиктовать через микрофон на клавиатуре.")
        return
    if duration > limit:
        await message.answer(f"Голосовое длиннее {limit // 60} мин. Разбей на части покороче, и я расшифрую каждую.")
        return
    ahead = transcribe.queue_size()
    note = await message.answer("Слушаю…" if not ahead else f"Слушаю… Передо мной ещё {ahead} голосовых, это займёт чуть дольше.")
    buf = io.BytesIO()
    await bot.download(media, destination=buf)
    try:
        text = await transcribe.transcribe(buf.getvalue())
    except transcribe.TranscribeError:
        await note.edit_text("Не получилось расшифровать. Попробуй ещё раз или напиши текстом.")
        return
    if not text:
        await note.edit_text("Ничего не расслышал. Попробуй записать ещё раз.")
        return
    async with SessionLocal() as s:
        user = await s.scalar(select(User).where(User.tg_id == message.from_user.id))
        if user:
            s.add(VoiceNote(user_id=user.id, duration=duration, text=text))
            await s.commit()
    forwarded = " пересланного" if message.forward_origin else ""
    await note.edit_text(f"Расшифровка{forwarded} голосового:\n\n«{text}»")
