import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["DEV_MODE"] = "true"
os.environ["BOT_TOKEN"] = "123456:TEST"
os.environ["ADMIN_IDS"] = "1"
os.environ["BOT_USERNAME"] = "elis_team_bot"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app import notify  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
async def db(monkeypatch):
    sent = []

    async def fake_send(tg_id, text, button=None):
        sent.append((tg_id, text))
        return True

    monkeypatch.setattr("app.routers.admin.send_message", fake_send)
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)
    from app import seed
    await seed.main()
    yield sent


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        yield c


def as_user(tg_id: int) -> dict:
    return {"X-Dev-User": str(tg_id)}
