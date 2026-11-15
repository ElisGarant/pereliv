from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import role_test
from ..db import get_session
from ..deps import current_user
from ..models import Application, Lesson, LessonProgress, Module, RoleTestResult, User

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])
REAPPLY_DAYS = 30


@router.get("/free-lessons")
async def free_lessons(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    rows = (await session.execute(
        select(Lesson).join(Module).where(Module.is_free.is_(True), Lesson.published.is_(True)).order_by(Module.position, Lesson.position)
    )).scalars().all()
    seen = set((await session.execute(
        select(LessonProgress.lesson_id).where(LessonProgress.user_id == user.id, LessonProgress.seen.is_(True))
    )).scalars().all())
    return [{"id": l.id, "title": l.title, "youtube_id": l.youtube_id, "duration_sec": l.duration_sec, "seen": l.id in seen} for l in rows]


@router.post("/free-lessons/{lesson_id}/seen")
async def mark_seen(lesson_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    lesson = await session.scalar(select(Lesson).join(Module).where(Lesson.id == lesson_id, Module.is_free.is_(True)))
    if not lesson:
        raise HTTPException(404, "Урок не найден")
    p = await session.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id))
    if not p:
        p = LessonProgress(user_id=user.id, lesson_id=lesson_id, attempts=0, best_score=0)
        session.add(p)
    p.seen = True
    await session.commit()
    return {"ok": True}


@router.get("/role-test")
async def get_role_test() -> dict:
    return {"questions": role_test.questions(), "directions": role_test.DIRS}


class RoleTestIn(BaseModel):
    answers: list[int]


@router.post("/role-test")
async def submit_role_test(body: RoleTestIn, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    try:
        res = role_test.score(body.answers)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    session.add(RoleTestResult(user_id=user.id, answers=body.answers, scores=res["scores"], top=res["top"], smart=res["smart"]))
    await session.commit()
    return res


class ApplicationIn(BaseModel):
    direction: Literal["inv", "msg", "call", "lead"]
    age_group: Literal["18–24", "25–34", "35+"]
    hours: str = Field(min_length=1, max_length=16)
    experience: str = Field(min_length=1, max_length=16)
    goal: str = Field(min_length=1, max_length=32)
    about: str = Field(default="", max_length=1000)
    adult_and_rules: bool


@router.post("/application", status_code=201)
async def apply(body: ApplicationIn, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    if not body.adult_and_rules:
        raise HTTPException(422, "Подтверди, что тебе есть 18 и ты согласен с правилами")
    if user.role != "guest":
        raise HTTPException(409, "Ты уже в команде")
    last = await session.scalar(select(Application).where(Application.user_id == user.id).order_by(Application.id.desc()).limit(1))
    if last and last.status in ("pending", "waitlist"):
        raise HTTPException(409, "Заявка уже на рассмотрении")
    if last and last.status == "rejected" and last.decided_at:
        decided = last.decided_at if last.decided_at.tzinfo else last.decided_at.replace(tzinfo=timezone.utc)
        retry = decided + timedelta(days=REAPPLY_DAYS)
        if datetime.now(timezone.utc) < retry:
            raise HTTPException(409, f"Повторно можно подать с {retry:%d.%m.%Y}")
    if not await session.scalar(select(RoleTestResult.id).where(RoleTestResult.user_id == user.id).limit(1)):
        raise HTTPException(422, "Сначала пройди тест на роль")
    a = Application(user_id=user.id, **body.model_dump(exclude={"adult_and_rules"}))
    session.add(a)
    await session.commit()
    return {"id": a.id, "status": a.status}
