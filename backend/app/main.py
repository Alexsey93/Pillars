from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine
from app.models import Pillar, Registry, User  # noqa: F401
from app.routers import pillars, registries
from app.schemas_user import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, fastapi_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_title, lifespan=lifespan)

# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

app.include_router(registries.router)
app.include_router(pillars.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}