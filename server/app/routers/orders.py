from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..deps import require
from ..models import Order, OrderMember, Report, User

router = APIRouter(prefix="/api/orders", tags=["orders"])


def order_out(o: Order, taken: int, mine: str | None) -> dict:
    return {"id": o.id, "type": o.type, "title": o.title, "client": o.client, "rate": o.rate, "unit": o.unit, "volume": o.volume,
            "deadline": o.deadline, "seats": o.seats, "taken": taken, "brief": o.brief, "rules": o.rules, "status": o.status, "my_status": mine}


@router.get("")
async def list_orders(user: User = Depends(require("member")), session: AsyncSession = Depends(get_session)) -> list[dict]:
    orders = (await session.execute(select(Order).where(Order.status == "open").order_by(Order.id.desc()))).scalars().all()
    counts = dict((await session.execute(
        select(OrderMember.order_id, func.count()).where(OrderMember.status.in_(("requested", "active"))).group_by(OrderMember.order_id)
    )).all())
    mine = dict((await session.execute(select(OrderMember.order_id, OrderMember.status).where(OrderMember.user_id == user.id))).all())
    return [order_out(o, counts.get(o.id, 0), mine.get(o.id)) for o in orders]


@router.post("/{order_id}/take")
async def take(order_id: int, user: User = Depends(require("member")), session: AsyncSession = Depends(get_session)) -> dict:
    o = await session.get(Order, order_id)
    if not o or o.status != "open":
        raise HTTPException(404, "Заказ не найден или закрыт")
    if await session.scalar(select(OrderMember).where(OrderMember.order_id == o.id, OrderMember.user_id == user.id)):
        raise HTTPException(409, "Ты уже откликнулся")
    taken = await session.scalar(select(func.count()).select_from(OrderMember).where(OrderMember.order_id == o.id, OrderMember.status.in_(("requested", "active"))))
    if taken >= o.seats:
        raise HTTPException(409, "Мест больше нет")
    session.add(OrderMember(order_id=o.id, user_id=user.id))
    await session.commit()
    return {"status": "requested"}


class ReportIn(BaseModel):
    numbers: dict[str, int] = Field(default_factory=dict)
    comment: str = Field(default="", max_length=2000)


@router.post("/{order_id}/reports", status_code=201)
async def report(order_id: int, body: ReportIn, user: User = Depends(require("member")), session: AsyncSession = Depends(get_session)) -> dict:
    m = await session.scalar(select(OrderMember).where(OrderMember.order_id == order_id, OrderMember.user_id == user.id))
    if not m or m.status != "active":
        raise HTTPException(403, "Отчёт можно сдать после подтверждения места менеджером")
    if any(v < 0 for v in body.numbers.values()):
        raise HTTPException(422, "Числа не могут быть отрицательными")
    r = Report(order_id=order_id, user_id=user.id, numbers=body.numbers, comment=body.comment)
    session.add(r)
    await session.commit()
    return {"id": r.id}
