from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import require
from ..models import Application, AuditLog, Lesson, Module, OrderMember, QuizQuestion, RoleTestResult, User
from ..notify import send_message
from ..youtube import youtube_id
from .me import user_out

router = APIRouter(prefix="/api/admin", tags=["admin"])
MSG = {
    "approved": ("Заявка одобрена! Академия открыта, первый урок уже ждёт.", "Открыть Академию"),
    "waitlist": ("Ты в листе ожидания. Напишем, как только освободится место.", None),
    "rejected": ("Спасибо за заявку. Сейчас не готовы взять, через 30 дней можно подать снова.", None),
}


@router.get("/applications")
async def applications(status: str = "pending", admin: User = Depends(require("manager")), session: AsyncSession = Depends(get_session)) -> list[dict]:
    rows = (await session.execute(select(Application, User).join(User, User.id == Application.user_id)
                                  .where(Application.status == status).order_by(Application.id))).all()
    out = []
    for a, u in rows:
        rt = await session.scalar(select(RoleTestResult).where(RoleTestResult.user_id == u.id).order_by(RoleTestResult.id.desc()).limit(1))
        out.append({"id": a.id, "user": user_out(u), "direction": a.direction, "age_group": a.age_group, "hours": a.hours, "experience": a.experience,
                    "goal": a.goal, "about": a.about, "status": a.status, "created_at": a.created_at.isoformat(),
                    "role_test": rt and {"top": rt.top, "scores": rt.scores, "smart": rt.smart}})
    return out


class DecisionIn(BaseModel):
    decision: Literal["approved", "waitlist", "rejected"]


@router.post("/applications/{app_id}/decision")
async def decide(app_id: int, body: DecisionIn, bg: BackgroundTasks, admin: User = Depends(require("manager")),
                 session: AsyncSession = Depends(get_session)) -> dict:
    a = await session.get(Application, app_id)
    if not a or a.status not in ("pending", "waitlist"):
        raise HTTPException(404, "Заявка не найдена или уже разобрана")
    u = await session.get(User, a.user_id)
    a.status, a.decided_by, a.decided_at = body.decision, admin.id, datetime.now(timezone.utc)
    if body.decision == "approved":
        u.role, u.direction = "student", a.direction
    session.add(AuditLog(actor_id=admin.id, action=f"application.{body.decision}", payload={"application_id": a.id, "user_id": u.id}))
    await session.commit()
    text, button = MSG[body.decision]
    bg.add_task(send_message, u.tg_id, text, button)
    return {"status": a.status}


@router.get("/people")
async def people(admin: User = Depends(require("manager")), session: AsyncSession = Depends(get_session)) -> list[dict]:
    return [user_out(u) for u in (await session.execute(select(User).order_by(User.id))).scalars().all()]


class RoleIn(BaseModel):
    role: Literal["guest", "student", "member", "mentor", "manager", "admin"]


@router.post("/people/{user_id}/role")
async def set_role(user_id: int, body: RoleIn, admin: User = Depends(require("admin")), session: AsyncSession = Depends(get_session)) -> dict:
    u = await session.get(User, user_id)
    if not u:
        raise HTTPException(404, "Человек не найден")
    session.add(AuditLog(actor_id=admin.id, action="user.role", payload={"user_id": u.id, "from": u.role, "to": body.role}))
    u.role = body.role
    await session.commit()
    return user_out(u)


@router.post("/order-members/{member_id}/confirm")
async def confirm_member(member_id: int, admin: User = Depends(require("manager")), session: AsyncSession = Depends(get_session)) -> dict:
    m = await session.get(OrderMember, member_id)
    if not m:
        raise HTTPException(404, "Отклик не найден")
    m.status = "active"
    session.add(AuditLog(actor_id=admin.id, action="order.confirm", payload={"member_id": m.id}))
    await session.commit()
    return {"status": m.status}


class QuestionIn(BaseModel):
    text: str = Field(min_length=1)
    options: list[str] = Field(min_length=2, max_length=6)
    correct: int = Field(ge=0)
    explanation: str = ""

    @field_validator("correct")
    @classmethod
    def in_range(cls, v, info):
        opts = info.data.get("options") or []
        if v >= len(opts):
            raise ValueError("верный ответ вне списка вариантов")
        return v


class LessonIn(BaseModel):
    module_id: int
    title: str = Field(min_length=1, max_length=200)
    position: int = 0
    youtube: str | None = None  # ссылка или id
    duration_sec: int = 0
    chapters: list[tuple[int, str]] = Field(default_factory=list)
    summary_md: str = ""
    task_text: str = ""
    materials: list[dict] = Field(default_factory=list)
    pass_score: int = Field(default=1, ge=1)
    retake_minutes: int = Field(default=60, ge=0)
    xp: int = Field(default=100, ge=0)
    published: bool = False
    questions: list[QuestionIn] = Field(default_factory=list)


def check_publishable(body: LessonIn, yt: str | None) -> None:
    missing = []
    if not yt:
        missing.append("видео по ссылке")
    if len(body.chapters) < 2:
        missing.append("хотя бы 2 главы")
    if len(body.summary_md.strip()) < 40:
        missing.append("конспект")
    if len(body.questions) < 3:
        missing.append("тест от 3 вопросов")
    if missing:
        raise HTTPException(422, "Не хватает для публикации: " + ", ".join(missing))


async def save_lesson(session: AsyncSession, lesson: Lesson, body: LessonIn) -> Lesson:
    if not await session.get(Module, body.module_id):
        raise HTTPException(404, "Модуль не найден")
    yt = youtube_id(body.youtube)
    if body.youtube and not yt:
        raise HTTPException(422, "Не похоже на ссылку YouTube")
    if body.published:
        check_publishable(body, yt)
    if body.questions and body.pass_score > len(body.questions):
        raise HTTPException(422, "Проходной балл больше числа вопросов")
    for k in ("module_id", "title", "position", "duration_sec", "summary_md", "task_text", "materials", "pass_score", "retake_minutes", "xp", "published"):
        setattr(lesson, k, getattr(body, k))
    lesson.youtube_id = yt
    lesson.chapters = [list(c) for c in sorted(body.chapters)]
    session.add(lesson)
    await session.flush()
    await session.execute(delete(QuizQuestion).where(QuizQuestion.lesson_id == lesson.id))
    for i, q in enumerate(body.questions):
        session.add(QuizQuestion(lesson_id=lesson.id, position=i, text=q.text, options=q.options, correct=q.correct, explanation=q.explanation))
    await session.commit()
    return lesson


@router.post("/lessons", status_code=201)
async def create_lesson(body: LessonIn, admin: User = Depends(require("admin")), session: AsyncSession = Depends(get_session)) -> dict:
    l = await save_lesson(session, Lesson(), body)
    return {"id": l.id, "youtube_id": l.youtube_id, "published": l.published}


@router.put("/lessons/{lesson_id}")
async def update_lesson(lesson_id: int, body: LessonIn, admin: User = Depends(require("admin")), session: AsyncSession = Depends(get_session)) -> dict:
    l = await session.get(Lesson, lesson_id)
    if not l:
        raise HTTPException(404, "Урок не найден")
    l = await save_lesson(session, l, body)
    return {"id": l.id, "youtube_id": l.youtube_id, "published": l.published}
