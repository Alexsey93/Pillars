from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import Pillar, Registry, User  # noqa: F401
from app.routers import export, photos, pillars, registries
from app.schemas_user import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, fastapi_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_title, lifespan=lifespan)

# ============================================================
# CORS MIDDLEWARE
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Если есть боевой домен фронтенда, добавьте его сюда:
        # "https://ваш-домен.ru",
    ],
    # Разрешает запросы с любого порта localhost / 127.0.0.1 во время разработки
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ROUTERS
# ============================================================

# Авторизация (логин / логаут)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Регистрация (с инвайт-кодом)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Управление пользователями
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Экспорт в Excel
app.include_router(export.router)

# Ваши роутеры (полный CRUD для всех авторизованных)
app.include_router(registries.router)
app.include_router(pillars.router)
app.include_router(photos.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
