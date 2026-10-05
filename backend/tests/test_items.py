from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Item


# ---------- CREATE ----------

async def test_create_item(client: AsyncClient):
    response = await client.post("/items/", json={"name": "Ноутбук"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Ноутбук"
    assert "id" in data


async def test_create_item_validation_error(client: AsyncClient):
    """Пустое имя должно вернуть 422."""
    response = await client.post("/items/", json={"name": ""})

    assert response.status_code == 422


# ---------- READ (список) ----------

async def test_list_items_empty(client: AsyncClient):
    response = await client.get("/items/")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_items(client: AsyncClient):
    await client.post("/items/", json={"name": "Мышь"})
    await client.post("/items/", json={"name": "Клавиатура"})

    response = await client.get("/items/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {item["name"] for item in data} == {"Мышь", "Клавиатура"}


async def test_list_items_pagination(client: AsyncClient):
    for i in range(5):
        await client.post("/items/", json={"name": f"Item {i}"})

    response = await client.get("/items/?skip=2&limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ---------- READ (один) ----------

async def test_get_item(client: AsyncClient):
    created = (await client.post("/items/", json={"name": "Монитор"})).json()

    response = await client.get(f"/items/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Монитор"


async def test_get_item_not_found(client: AsyncClient):
    response = await client.get("/items/9999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


# ---------- UPDATE ----------

async def test_update_item(client: AsyncClient):
    created = (await client.post("/items/", json={"name": "Старое"})).json()

    response = await client.patch(
        f"/items/{created['id']}", json={"name": "Новое"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Новое"


async def test_update_item_not_found(client: AsyncClient):
    response = await client.patch("/items/9999", json={"name": "X"})

    assert response.status_code == 404


# ---------- DELETE ----------

async def test_delete_item(client: AsyncClient):
    created = (await client.post("/items/", json={"name": "Удалить"})).json()

    response = await client.delete(f"/items/{created['id']}")
    assert response.status_code == 204

    # проверяем, что его больше нет
    response = await client.get(f"/items/{created['id']}")
    assert response.status_code == 404


async def test_delete_item_not_found(client: AsyncClient):
    response = await client.delete("/items/9999")

    assert response.status_code == 404
