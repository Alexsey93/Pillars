from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import create_db_and_tables, engine
from app.models import Item  # noqa: F401 — регистрирует модель в SQLModel
from app.routers import items


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_title, lifespan=lifespan)

app.include_router(items.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
