"""Отправка сообщений пользователям через Bot API. Без токена просто пишет в лог."""
import logging

import httpx

from .config import get_settings

log = logging.getLogger(__name__)


async def send_message(tg_id: int, text: str, webapp_button: str | None = None) -> bool:
    s = get_settings()
    if not s.bot_token:
        log.info("notify %s: %s", tg_id, text)
        return False
    payload: dict = {"chat_id": tg_id, "text": text}
    if webapp_button:
        payload["reply_markup"] = {"inline_keyboard": [[{"text": webapp_button, "web_app": {"url": s.webapp_url}}]]}
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"https://api.telegram.org/bot{s.bot_token}/sendMessage", json=payload)
        return r.status_code == 200
    except httpx.HTTPError:
        log.exception("не удалось отправить сообщение %s", tg_id)
        return False
