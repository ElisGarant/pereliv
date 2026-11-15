from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_session
from .models import User
from .telegram_auth import InitDataError, validate_init_data

RANK = {"guest": 0, "student": 1, "member": 2, "mentor": 3, "manager": 4, "admin": 5}


async def upsert_user(session: AsyncSession, tg: dict) -> User:
    user = await session.scalar(select(User).where(User.tg_id == int(tg["id"])))
    if user is None:
        user = User(tg_id=int(tg["id"]))
        session.add(user)
    user.username = tg.get("username") or user.username
    user.first_name = tg.get("first_name") or user.first_name or ""
    user.last_name = tg.get("last_name") or user.last_name
    user.photo_url = tg.get("photo_url") or user.photo_url
    if user.tg_id in get_settings().admin_id_set:
        user.role = "admin"
    await session.flush()
    if not user.ref_code:
        user.ref_code = f"ELS{user.id:04d}"
    await session.commit()
    return user


async def current_user(
    authorization: str | None = Header(default=None),
    x_dev_user: str | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    s = get_settings()
    if authorization and authorization.lower().startswith("tma "):
        try:
            data = validate_init_data(authorization[4:], s.bot_token, s.initdata_ttl)
        except InitDataError as e:
            raise HTTPException(401, f"Не удалось проверить вход: {e}") from e
        return await upsert_user(session, data["user"])
    if s.dev_mode and x_dev_user:
        return await upsert_user(session, {"id": int(x_dev_user), "first_name": "Dev"})
    raise HTTPException(401, "Открой приложение из Telegram")


def require(role: str):
    async def dep(user: User = Depends(current_user)) -> User:
        if RANK.get(user.role, 0) < RANK[role]:
            raise HTTPException(403, "Недостаточно прав")
        return user

    return dep
