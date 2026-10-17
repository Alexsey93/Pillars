from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.config import settings
from app.database import get_session
from app.main import app
from app.models import User, DownloadToken, Pillar, Registry  # noqa: F401
from app.users import UserManager, get_user_db


# ============================================================
# ДВИЖОК
# ============================================================

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    await engine.dispose()


# ============================================================
# СЕССИЯ (с откатом)
# ============================================================

@pytest_asyncio.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session


# ============================================================
# HTTP-КЛИЕНТ (С АВТОРИЗАЦИЕЙ)
# ============================================================

@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    
    # Создаем клиент
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Регистрируем тестового пользователя (чтобы пройти auth)
        await ac.post(
            "/auth/register",
            json={
                "email": "testuser",
                "password": "testpassword",
                "invite_code": settings.invite_code,
            },
        )
        
        # 2. Логинимся, чтобы получить токен
        login_resp = await ac.post(
            "/auth/jwt/login",
            data={"username": "testuser", "password": "testpassword"},
        )
        token = login_resp.json()["access_token"]
        
        # 3. Устанавливаем заголовок Authorization для всех последующих запросов
        ac.headers["Authorization"] = f"Bearer {token}"

        yield ac

    app.dependency_overrides.clear()