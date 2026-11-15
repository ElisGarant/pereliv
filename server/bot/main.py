"""Запуск: python -m bot.main"""
import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import get_settings
from app.db import create_all

from .handlers import start, voice


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    s = get_settings()
    if not s.bot_token:
        raise SystemExit("Заполни BOT_TOKEN в server/.env")
    if s.database_url.startswith("sqlite"):
        await create_all()
    bot = Bot(s.bot_token)
    dp = Dispatcher()
    dp.include_routers(start.router, voice.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
