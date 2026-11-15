from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import RANK, require
from ..models import Lesson, LessonProgress, Module, Note, QuizQuestion, User

router = APIRouter(prefix="/api/academy", tags=["academy"])


async def course(session: AsyncSession, user: User) -> list[tuple[Module, list[tuple[Lesson, str]]]]:
    """Модули и уроки пользователя со статусами done / current / locked. Уроки открываются строго по порядку."""
    q = select(Module).where(Module.is_free.is_(False)).order_by(Module.position)
    if RANK[user.role] < RANK["admin"]:
        q = q.where(or_(Module.direction.is_(None), Module.direction == user.direction))
    modules = (await session.execute(q)).scalars().all()
    done = set((await session.execute(
        select(LessonProgress.lesson_id).where(LessonProgress.user_id == user.id, LessonProgress.completed_at.is_not(None))
    )).scalars().all())
    out, current_given = [], False
    for m in modules:
        lessons = (await session.execute(
            select(Lesson).where(Lesson.module_id == m.id, Lesson.published.is_(True)).order_by(Lesson.position)
        )).scalars().all()
        items = []
        for l in lessons:
            if l.id in done:
                st = "done"
            elif not current_given:
                st, current_given = "current", True
            else:
                st = "locked"
            items.append((l, st))
        out.append((m, items))
    return out


@router.get("/modules")
async def modules(user: User = Depends(require("student")), session: AsyncSession = Depends(get_session)) -> list[dict]:
    return [{"id": m.id, "title": m.title, "lessons": [{"id": l.id, "title": l.title, "duration_sec": l.duration_sec, "status": st} for l, st in items]}
            for m, items in await course(session, user)]


async def lesson_for(session: AsyncSession, user: User, lesson_id: int) -> tuple[Lesson, str]:
    for _, items in await course(session, user):
        for l, st in items:
            if l.id == lesson_id:
                if st == "locked":
                    raise HTTPException(403, "Урок откроется после предыдущего")
                return l, st
    raise HTTPException(404, "Урок не найден")


@router.get("/lessons/{lesson_id}")
async def lesson(lesson_id: int, user: User = Depends(require("student")), session: AsyncSession = Depends(get_session)) -> dict:
    l, st = await lesson_for(session, user, lesson_id)
    qs = (await session.execute(select(QuizQuestion).where(QuizQuestion.lesson_id == l.id).order_by(QuizQuestion.position))).scalars().all()
    p = await session.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_id == l.id))
    return {"id": l.id, "title": l.title, "status": st, "youtube_id": l.youtube_id, "duration_sec": l.duration_sec, "chapters": l.chapters,
            "summary_md": l.summary_md, "task_text": l.task_text, "materials": l.materials, "xp": l.xp,
            "quiz": {"pass_score": l.pass_score, "retake_minutes": l.retake_minutes, "questions": [{"id": q.id, "text": q.text, "options": q.options} for q in qs],
                     "best_score": p.best_score if p else 0, "attempts": p.attempts if p else 0}}


class QuizIn(BaseModel):
    answers: list[int]


@router.post("/lessons/{lesson_id}/quiz")
async def submit_quiz(lesson_id: int, body: QuizIn, user: User = Depends(require("student")), session: AsyncSession = Depends(get_session)) -> dict:
    l, _ = await lesson_for(session, user, lesson_id)
    qs = (await session.execute(select(QuizQuestion).where(QuizQuestion.lesson_id == l.id).order_by(QuizQuestion.position))).scalars().all()
    if len(body.answers) != len(qs):
        raise HTTPException(422, f"Нужно {len(qs)} ответов")
    p = await session.scalar(select(LessonProgress).where(LessonProgress.user_id == user.id, LessonProgress.lesson_id == l.id))
    if not p:
        p = LessonProgress(user_id=user.id, lesson_id=l.id, seen=False, attempts=0, best_score=0)
        session.add(p)
    now = datetime.now(timezone.utc)
    if p.last_attempt_at and not p.completed_at:
        last = p.last_attempt_at if p.last_attempt_at.tzinfo else p.last_attempt_at.replace(tzinfo=timezone.utc)
        retry = last + timedelta(minutes=l.retake_minutes)
        if now < retry:
            raise HTTPException(429, f"Пересдача с {retry:%H:%M} UTC")
    results = [{"correct": q.correct, "ok": a == q.correct, "explanation": q.explanation} for q, a in zip(qs, body.answers)]
    score = sum(r["ok"] for r in results)
    passed = score >= l.pass_score
    p.attempts += 1
    p.best_score = max(p.best_score, score)
    p.last_attempt_at = now
    if passed and not p.completed_at:
        p.completed_at = now
    await session.commit()
    return {"score": score, "total": len(qs), "passed": passed, "results": results, "xp": l.xp if passed else 0}


class NoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    t_sec: int | None = Field(default=None, ge=0)


@router.get("/lessons/{lesson_id}/notes")
async def notes(lesson_id: int, user: User = Depends(require("student")), session: AsyncSession = Depends(get_session)) -> list[dict]:
    rows = (await session.execute(select(Note).where(Note.user_id == user.id, Note.lesson_id == lesson_id).order_by(Note.t_sec.is_(None), Note.t_sec, Note.id))).scalars().all()
    return [{"id": n.id, "t_sec": n.t_sec, "text": n.text} for n in rows]


@router.post("/lessons/{lesson_id}/notes", status_code=201)
async def add_note(lesson_id: int, body: NoteIn, user: User = Depends(require("student")), session: AsyncSession = Depends(get_session)) -> dict:
    await lesson_for(session, user, lesson_id)
    n = Note(user_id=user.id, lesson_id=lesson_id, text=body.text.strip(), t_sec=body.t_sec)
    session.add(n)
    await session.commit()
    return {"id": n.id, "t_sec": n.t_sec, "text": n.text}


@router.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int, user: User = Depends(require("student")), session: AsyncSession = Depends(get_session)) -> None:
    n = await session.get(Note, note_id)
    if not n or n.user_id != user.id:  # чужие заметки не видны и не удаляются
        raise HTTPException(404, "Заметка не найдена")
    await session.delete(n)
    await session.commit()
