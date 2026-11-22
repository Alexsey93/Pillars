import io

from httpx import AsyncClient

from app.config import settings


async def _register_and_login(client: AsyncClient, email: str, password: str) -> str:
    await client.post(
        "/auth/register",
        json={"email": email, "password": password, "invite_code": settings.invite_code},
    )
    resp = await client.post("/auth/jwt/login", data={"username": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _create_registry(client: AsyncClient, token: str) -> int:
    resp = await client.post(
        "/registries/",
        json={"region": "Москва", "street": "Экспортная"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_download_token_one_time(client: AsyncClient):
    """Токен скачивания одноразовый: второй запрос — 400."""
    token = await _register_and_login(client, "export@example.com", "secret123")
    reg_id = await _create_registry(client, token)

    link_resp = await client.post(
        f"/export/registry/{reg_id}/link",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert link_resp.status_code == 200
    url = link_resp.json()["url"]

    resp1 = await client.get(url)
    assert resp1.status_code == 200

    resp2 = await client.get(url)
    assert resp2.status_code == 400
    assert "already used" in resp2.json()["detail"]


async def test_download_link_foreign_registry_forbidden(client: AsyncClient):
    """Нельзя создать ссылку на чужой реестр — 403."""
    token_a = await _register_and_login(client, "exp_a@example.com", "secret123")
    reg_a = await _create_registry(client, token_a)

    token_b = await _register_and_login(client, "exp_b@example.com", "secret123")

    resp = await client.post(
        f"/export/registry/{reg_a}/link",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403


async def test_download_invalid_token(client: AsyncClient):
    """Несуществующий токен — 404."""
    resp = await client.get("/export/download/abc123invalid")
    assert resp.status_code == 404