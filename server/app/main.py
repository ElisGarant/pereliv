from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import create_all
from .routers import academy, admin, me, onboarding, orders


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().database_url.startswith("sqlite"):
        await create_all()  # для локальной разработки; в Supabase схема ставится миграцией
    yield


app = FastAPI(title="ELI_S team API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in get_settings().cors_origins.split(",") if o.strip()],
                   allow_methods=["*"], allow_headers=["*"])
for r in (me.router, onboarding.router, academy.router, orders.router, admin.router):
    app.include_router(r)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
