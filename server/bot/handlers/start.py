from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.deps import upsert_user
from app.models import User

router = Router()


def open_app_kb(text: str = "Открыть ELI_S team") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, web_app=WebAppInfo(url=get_settings().webapp_url))]])


async def register(message: Message, ref: str | None) -> tuple[User, User | None]:
    tg = message.from_user
    async with SessionLocal() as s:
        existed = await s.scalar(select(User.id).where(User.tg_id == tg.id))
        user = await upsert_user(s, {"id": tg.id, "username": tg.username, "first_name": tg.first_name, "last_name": tg.last_name})
        referrer = None
        if ref and not existed:  # реферал закрепляется только при первом входе
            referrer = await s.scalar(select(User).where(User.ref_code == ref.upper()))
            if referrer and referrer.id != user.id:  # самореферал запрещён
                user.referrer_id = referrer.id
                await s.commit()
            else:
                referrer = None
        return user, referrer


@router.message(CommandStart())
async def start(message: Message, command: CommandObject) -> None:
    user, referrer = await register(message, command.args)
    who = f" Тебя пригласил {referrer.first_name}." if referrer else ""
    if user.role == "guest":
        text = f"Привет! Это ELI_S team: учим продавать и сразу даём заказы.{who}\n\nЗа 10 минут: 3 коротких урока, тест на роль и анкета."
    else:
        text = "С возвращением! Открывай приложение, всё на месте."
    await message.answer(text, reply_markup=open_app_kb())


@router.message(Command("app"))
async def app_cmd(message: Message) -> None:
    await message.answer("Приложение команды:", reply_markup=open_app_kb())


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "Что умеет бот:\n"
        "• /app — открыть приложение\n"
        "• Голосовое или пересланное голосовое — переведу в текст\n"
        "• Ответы по заявке, новые уроки и заказы приходят сюда\n\n"
        "Писать админу в личку можно напрямую."
    )
