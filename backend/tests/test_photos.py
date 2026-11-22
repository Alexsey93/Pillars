import io

from httpx import AsyncClient

from app.config import settings


# ============================================================
# ХЕЛПЕРЫ
# ============================================================

async def _register_and_login(client: AsyncClient, email: str, password: str) -> str:
    """Регистрирует пользователя (если ещё нет) и возвращает JWT."""
    await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "invite_code": settings.invite_code,
        },
    )
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _create_registry(client: AsyncClient, token: str) -> int:
    resp = await client.post(
        "/registries/",
        json={"region": "Москва", "street": "Тестовая"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_pillar(client: AsyncClient, token: str, registry_id: int) -> int:
    resp = await client.post(
        "/pillars/",
        json={"registry_id": registry_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _fake_png() -> bytes:
    """Минимальный валидный PNG (1x1, прозрачный)."""
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c6360000000020001e221bc330000000049454e44ae426082"
    )


# ============================================================
# ТЕСТЫ
# ============================================================

async def test_upload_photo_to_own_pillar(client: AsyncClient):
    """Владелец реестра может загрузить фото к своей опоре."""
    token = await _register_and_login(client, "owner@example.com", "secret123")
    registry_id = await _create_registry(client, token)
    pillar_id = await _create_pillar(client, token, registry_id)

    resp = await client.post(
        f"/pillars/{pillar_id}/photo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("photo.png", io.BytesIO(_fake_png()), "image/png")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["url"].startswith("/pillars/photo/")
    assert data["filename"].endswith(".png")


async def test_upload_photo_to_foreign_pillar_forbidden(client: AsyncClient):
    """Чужой пользователь НЕ может загрузить фото к чужой опоре (403)."""
    token_a = await _register_and_login(client, "alice@example.com", "secret123")
    reg_a = await _create_registry(client, token_a)
    pillar_a = await _create_pillar(client, token_a, reg_a)

    token_b = await _register_and_login(client, "bob@example.com", "secret123")

    resp = await client.post(
        f"/pillars/{pillar_a}/photo",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("photo.png", io.BytesIO(_fake_png()), "image/png")},
    )
    assert resp.status_code == 403, resp.text
    assert "Access denied" in resp.json()["detail"]


async def test_upload_photo_unauthorized(client: AsyncClient):
    """Без токена — 401."""
    token = await _register_and_login(client, "carol@example.com", "secret123")
    reg = await _create_registry(client, token)
    pillar = await _create_pillar(client, token, reg)

    resp = await client.post(
        f"/pillars/{pillar}/photo",
        headers={"Authorization": ""},
        files={"file": ("photo.png", io.BytesIO(_fake_png()), "image/png")},
    )
    assert resp.status_code == 401


async def test_upload_photo_to_nonexistent_pillar(client: AsyncClient):
    """Несуществующая опора — 404 (до проверки доступа)."""
    token = await _register_and_login(client, "dave@example.com", "secret123")

    resp = await client.post(
        "/pillars/9999/photo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("photo.png", io.BytesIO(_fake_png()), "image/png")},
    )
    assert resp.status_code == 404


async def test_upload_photo_invalid_format(client: AsyncClient):
    """Невалидное расширение — 400."""
    token = await _register_and_login(client, "eve@example.com", "secret123")
    reg = await _create_registry(client, token)
    pillar = await _create_pillar(client, token, reg)

    resp = await client.post(
        f"/pillars/{pillar}/photo",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("evil.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "Invalid file format" in resp.json()["detail"]