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

from app.database import get_session
from app.main import app
from app.models import Item  # noqa: F401


# ============================================================
# ДВИЖОК (один на всю сессию тестов)
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
# СЕССИЯ — чистим таблицы перед КАЖДЫМ тестом
# ============================================================

@pytest_asyncio.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    # 1. Удаляем все таблицы и создаём заново — гарантированно чистая БД
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    # 2. Отдаём сессию тесту
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session


# ============================================================
# HTTP-КЛИЕНТ
# ============================================================

@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
