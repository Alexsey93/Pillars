from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import create_db_and_tables, engine
from app.models import Pillar, Registry  # noqa: F401
from app.routers import pillars, registries


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_title, lifespan=lifespan)

app.include_router(registries.router)
app.include_router(pillars.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}