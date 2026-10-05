from httpx import AsyncClient


# ============================================================
# CREATE
# ============================================================

async def test_create_pillar_full(client: AsyncClient):
    """Создание опоры со всеми полями."""
    payload = {
        "region": "Московская область",
        "raion": "Одинцовский",
        "city": "Одинцово",
        "address": "ул. Ленина, д. 5, опора 12",
        "latitude": 55.6789,
        "longitude": 37.2634,
        "owner": "ПАО Ростелеком",
        "number_owner_pilar": "RT-123456",
        "material": "Железобетон",
        "height": 9.5,
        "class_voltage": "0.4 кВ",
        "cnt_fastening": 3,
        "cnt_vok_not_ab": 2,
        "cnt_mzhk_not_ab": 1,
        "cnt_ab_vok_mzhk": 15,
        "cnt_o_coup": 1,
        "cnt_shk": 0,
        "cnt_ork": 2,
    }
    response = await client.post("/pillars/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["region"] == "Московская область"
    assert data["city"] == "Одинцово"
    assert data["latitude"] == 55.6789
    assert data["material"] == "Железобетон"
    assert data["height"] == 9.5
    assert data["class_voltage"] == "0.4 кВ"
    assert data["cnt_vok_not_ab"] == 2
    assert data["cnt_shk"] == 0
    assert "id" in data
    assert "created_at" in data
    assert data["updated_at"] is None


async def test_create_pillar_minimal(client: AsyncClient):
    """Обязательно только поле region."""
    response = await client.post("/pillars/", json={"region": "Москва"})

    assert response.status_code == 201
    data = response.json()
    assert data["region"] == "Москва"
    assert data["raion"] is None
    assert data["cnt_fastening"] == 0
    assert data["cnt_shk"] == 0


async def test_create_pillar_invalid_region(client: AsyncClient):
    """Регион должен быть из enum."""
    response = await client.post("/pillars/", json={"region": "Атлантида"})
    assert response.status_code == 422


async def test_create_pillar_invalid_latitude(client: AsyncClient):
    """Широта должна быть в диапазоне -90..90."""
    response = await client.post(
        "/pillars/", json={"region": "Москва", "latitude": 100}
    )
    assert response.status_code == 422


async def test_create_pillar_negative_counter(client: AsyncClient):
    """Счётчики не могут быть отрицательными."""
    response = await client.post(
        "/pillars/", json={"region": "Москва", "cnt_shk": -1}
    )
    assert response.status_code == 422


async def test_create_pillar_invalid_material(client: AsyncClient):
    """Материал должен быть из enum."""
    response = await client.post(
        "/pillars/",
        json={"region": "Москва", "material": "Пластилин"},
    )
    assert response.status_code == 422


# ============================================================
# READ (список)
# ============================================================

async def test_list_pillars_empty(client: AsyncClient):
    response = await client.get("/pillars/")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_pillars(client: AsyncClient):
    await client.post("/pillars/", json={"region": "Москва"})
    await client.post("/pillars/", json={"region": "Московская область"})

    response = await client.get("/pillars/")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_pillars_pagination(client: AsyncClient):
    for _ in range(5):
        await client.post("/pillars/", json={"region": "Москва"})

    response = await client.get("/pillars/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ============================================================
# READ (один)
# ============================================================

async def test_get_pillar(client: AsyncClient):
    created = (
        await client.post("/pillars/", json={"region": "Москва"})
    ).json()

    response = await client.get(f"/pillars/{created['id']}")
    assert response.status_code == 200
    assert response.json()["region"] == "Москва"


async def test_get_pillar_not_found(client: AsyncClient):
    response = await client.get("/pillars/9999")
    assert response.status_code == 404


# ============================================================
# UPDATE
# ============================================================

async def test_update_pillar(client: AsyncClient):
    created = (
        await client.post("/pillars/", json={"region": "Москва"})
    ).json()

    response = await client.patch(
        f"/pillars/{created['id']}",
        json={"city": "Зеленоград", "cnt_shk": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Зеленоград"
    assert data["cnt_shk"] == 5
    assert data["updated_at"] is not None


async def test_update_pillar_partial(client: AsyncClient):
    """PATCH одного поля не затирает остальные."""
    created = (
        await client.post(
            "/pillars/",
            json={"region": "Москва", "city": "Москва", "cnt_shk": 3},
        )
    ).json()

    updated = (
        await client.patch(
            f"/pillars/{created['id']}", json={"cnt_shk": 7}
        )
    ).json()

    assert updated["region"] == "Москва"
    assert updated["city"] == "Москва"
    assert updated["cnt_shk"] == 7


async def test_update_pillar_not_found(client: AsyncClient):
    response = await client.patch("/pillars/9999", json={"cnt_shk": 1})
    assert response.status_code == 404


# ============================================================
# DELETE
# ============================================================

async def test_delete_pillar(client: AsyncClient):
    created = (
        await client.post("/pillars/", json={"region": "Москва"})
    ).json()

    response = await client.delete(f"/pillars/{created['id']}")
    assert response.status_code == 204

    # проверяем, что его больше нет
    response = await client.get(f"/pillars/{created['id']}")
    assert response.status_code == 404


async def test_delete_pillar_not_found(client: AsyncClient):
    response = await client.delete("/pillars/9999")
    assert response.status_code == 404