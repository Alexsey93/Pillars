from httpx import AsyncClient


# ============================================================
# ХЕЛПЕР
# ============================================================

async def _create_registry(client: AsyncClient) -> int:
    """Создаёт тестовый реестр и возвращает его id."""
    r = await client.post(
        "/registries/",
        json={
            "region": "Московская область",
            "raion": "Одинцовский",
            "city": "Одинцово",
            "street": "ул. Ленина",
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


# ============================================================
# CREATE
# ============================================================

async def test_create_pillar_full(client: AsyncClient):
    registry_id = await _create_registry(client)

    payload = {
        "registry_id": registry_id,
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
    assert data["registry_id"] == registry_id
    assert data["latitude"] == 55.6789
    assert data["longitude"] == 37.2634
    assert data["material"] == "Железобетон"
    assert data["height"] == 9.5
    assert data["class_voltage"] == "0.4 кВ"
    assert data["cnt_vok_not_ab"] == 2
    assert data["cnt_shk"] == 0
    assert "id" in data
    assert "created_at" in data
    assert data["updated_at"] is None


async def test_create_pillar_minimal(client: AsyncClient):
    """Обязателен только registry_id."""
    registry_id = await _create_registry(client)

    response = await client.post(
        "/pillars/", json={"registry_id": registry_id}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["registry_id"] == registry_id
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["cnt_fastening"] == 0


async def test_create_pillar_without_coordinates(client: AsyncClient):
    """Координаты опциональны."""
    registry_id = await _create_registry(client)

    response = await client.post(
        "/pillars/",
        json={"registry_id": registry_id, "material": "Дерево"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["latitude"] is None
    assert data["longitude"] is None
    assert data["material"] == "Дерево"


async def test_create_pillar_invalid_registry(client: AsyncClient):
    """Несуществующий реестр — 404."""
    response = await client.post(
        "/pillars/", json={"registry_id": 9999}
    )
    assert response.status_code == 404


async def test_create_pillar_invalid_latitude(client: AsyncClient):
    registry_id = await _create_registry(client)

    response = await client.post(
        "/pillars/",
        json={"registry_id": registry_id, "latitude": 100},
    )
    assert response.status_code == 422


async def test_create_pillar_negative_counter(client: AsyncClient):
    registry_id = await _create_registry(client)

    response = await client.post(
        "/pillars/",
        json={"registry_id": registry_id, "cnt_shk": -1},
    )
    assert response.status_code == 422


async def test_create_pillar_invalid_material(client: AsyncClient):
    registry_id = await _create_registry(client)

    response = await client.post(
        "/pillars/",
        json={"registry_id": registry_id, "material": "Пластилин"},
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
    registry_id = await _create_registry(client)
    await client.post("/pillars/", json={"registry_id": registry_id})
    await client.post("/pillars/", json={"registry_id": registry_id})

    response = await client.get("/pillars/")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_pillars_filter_by_registry(client: AsyncClient):
    """Фильтр по registry_id возвращает только опоры этого реестра."""
    reg1 = await _create_registry(client)
    reg2 = await _create_registry(client)

    await client.post("/pillars/", json={"registry_id": reg1})
    await client.post("/pillars/", json={"registry_id": reg1})
    await client.post("/pillars/", json={"registry_id": reg2})

    response = await client.get(f"/pillars/?registry_id={reg1}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(p["registry_id"] == reg1 for p in data)


async def test_list_pillars_pagination(client: AsyncClient):
    registry_id = await _create_registry(client)
    for _ in range(5):
        await client.post("/pillars/", json={"registry_id": registry_id})

    response = await client.get("/pillars/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ============================================================
# READ (один)
# ============================================================

async def test_get_pillar(client: AsyncClient):
    registry_id = await _create_registry(client)
    created = (
        await client.post("/pillars/", json={"registry_id": registry_id})
    ).json()

    response = await client.get(f"/pillars/{created['id']}")
    assert response.status_code == 200
    assert response.json()["registry_id"] == registry_id


async def test_get_pillar_not_found(client: AsyncClient):
    response = await client.get("/pillars/9999")
    assert response.status_code == 404


# ============================================================
# UPDATE
# ============================================================

async def test_update_pillar(client: AsyncClient):
    registry_id = await _create_registry(client)
    created = (
        await client.post("/pillars/", json={"registry_id": registry_id})
    ).json()

    response = await client.patch(
        f"/pillars/{created['id']}",
        json={"latitude": 55.75, "longitude": 37.61, "cnt_shk": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 55.75
    assert data["longitude"] == 37.61
    assert data["cnt_shk"] == 5
    assert data["updated_at"] is not None


async def test_update_pillar_partial(client: AsyncClient):
    """PATCH одного поля не затирает остальные."""
    registry_id = await _create_registry(client)
    created = (
        await client.post(
            "/pillars/",
            json={"registry_id": registry_id, "cnt_shk": 3, "material": "Дерево"},
        )
    ).json()

    updated = (
        await client.patch(
            f"/pillars/{created['id']}", json={"cnt_shk": 7}
        )
    ).json()

    assert updated["material"] == "Дерево"
    assert updated["cnt_shk"] == 7
    assert updated["registry_id"] == registry_id


async def test_update_pillar_change_registry(client: AsyncClient):
    """Можно перепривязать опору к другому реестру."""
    reg1 = await _create_registry(client)
    reg2 = await _create_registry(client)
    created = (
        await client.post("/pillars/", json={"registry_id": reg1})
    ).json()

    updated = (
        await client.patch(
            f"/pillars/{created['id']}", json={"registry_id": reg2}
        )
    ).json()

    assert updated["registry_id"] == reg2


async def test_update_pillar_invalid_registry(client: AsyncClient):
    registry_id = await _create_registry(client)
    created = (
        await client.post("/pillars/", json={"registry_id": registry_id})
    ).json()

    response = await client.patch(
        f"/pillars/{created['id']}", json={"registry_id": 9999}
    )
    assert response.status_code == 404


async def test_update_pillar_not_found(client: AsyncClient):
    response = await client.patch("/pillars/9999", json={"cnt_shk": 1})
    assert response.status_code == 404


# ============================================================
# DELETE
# ============================================================

async def test_delete_pillar(client: AsyncClient):
    registry_id = await _create_registry(client)
    created = (
        await client.post("/pillars/", json={"registry_id": registry_id})
    ).json()

    response = await client.delete(f"/pillars/{created['id']}")
    assert response.status_code == 204

    response = await client.get(f"/pillars/{created['id']}")
    assert response.status_code == 404


async def test_delete_pillar_not_found(client: AsyncClient):
    response = await client.delete("/pillars/9999")
    assert response.status_code == 404