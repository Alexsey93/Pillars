import os
import tempfile
from typing import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.config import settings
from app.database import get_session
from app.main import app
from app.models import User, DownloadToken, Pillar, Registry  # noqa: F401
from app.users import UserManager, get_user_db


# ============================================================
# ДВИЖОК (файловая SQLite + NullPool — изоляция сессий как в проде)
# ============================================================

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )

    # SQLite по умолчанию НЕ включает FK — включаем на КАЖДОМ соединении
    @event.listens_for(engine.sync_engine, "connect")
    def _fk_pragma_on_connect(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    yield engine

    await engine.dispose()
    try:
        os.unlink(db_path)
    except OSError:
        pass


# ============================================================
# СБРОС СХЕМЫ ПЕРЕД КАЖДЫМ ТЕСТОМ
# ============================================================

@pytest_asyncio.fixture(autouse=True)
async def _reset_db(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    yield


# ============================================================
# HTTP-КЛИЕНТ (С АВТОРИЗАЦИЕЙ, новая сессия на каждый запрос)
# ============================================================

@pytest_asyncio.fixture
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        async with AsyncSession(test_engine, expire_on_commit=False) as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        reg_resp = await ac.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "testpassword",
                "invite_code": settings.invite_code,
            },
        )
        print(f"\n[DEBUG] register status: {reg_resp.status_code}, body: {reg_resp.text!r}")

        login_resp = await ac.post(
            "/auth/jwt/login",
            data={"username": "test@example.com", "password": "testpassword"},
        )
        print(f"[DEBUG] login status: {login_resp.status_code}, body: {login_resp.text!r}")

        token = login_resp.json()["access_token"]
        ac.headers["Authorization"] = f"Bearer {token}"

        # --- ВРЕМЕННЫЙ ДЕБАГ: что реально в БД ---
        async with AsyncSession(test_engine) as s:
            users = (await s.execute(text('SELECT id, email FROM "user"'))).all()
            print(f"[DEBUG] users in DB: {users!r}")

            regs = (await s.execute(text("SELECT id, owner_id, street FROM registry"))).all()
            print(f"[DEBUG] registries in DB: {regs!r}")

            # Проверим, как SQLite видит типы колонок
            cols = (await s.execute(text("PRAGMA table_info('user')"))).all()
            print(f"[DEBUG] PRAGMA table_info('user') id: {[c for c in cols if c[1] == 'id']!r}")

            cols = (await s.execute(text("PRAGMA table_info('registry')"))).all()
            print(f"[DEBUG] PRAGMA table_info('registry') owner_id: {[c for c in cols if c[1] == 'owner_id']!r}")
        # --- /ВРЕМЕННЫЙ ДЕБАГ ---

        yield ac

    app.dependency_overrides.clear()