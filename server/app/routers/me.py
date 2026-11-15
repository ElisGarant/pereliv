from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db import get_session
from ..deps import current_user
from ..models import Application, User

router = APIRouter(prefix="/api", tags=["me"])


def user_out(u: User) -> dict:
    return {"id": u.id, "tg_id": u.tg_id, "username": u.username, "first_name": u.first_name, "last_name": u.last_name,
            "photo_url": u.photo_url, "role": u.role, "direction": u.direction, "ref_code": u.ref_code}


@router.get("/me")
async def me(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    app = await session.scalar(select(Application).where(Application.user_id == user.id).order_by(Application.id.desc()).limit(1))
    bot = get_settings().bot_username
    return {"user": user_out(user),
            "application": app and {"id": app.id, "status": app.status, "direction": app.direction, "created_at": app.created_at.isoformat()},
            "ref_link": f"https://t.me/{bot}?start={user.ref_code}" if bot else None}
