from httpx import AsyncClient


# ============================================================
# CREATE
# ============================================================

async def test_create_registry_full(client: AsyncClient):
    payload = {
        "region": "Московская область",
        "raion": "Одинцовский",
        "city": "Одинцово",
        "street": "ул. Ленина",
    }
    response = await client.post("/registries/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["region"] == "Московская область"
    assert data["raion"] == "Одинцовский"
    assert data["city"] == "Одинцово"
    assert data["street"] == "ул. Ленина"
    assert "id" in data
    assert "created_at" in data
    assert data["updated_at"] is None


async def test_create_registry_minimal(client: AsyncClient):
    """Обязательны только region и street."""
    response = await client.post(
        "/registries/",
        json={"region": "Москва", "street": "Тверская"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["region"] == "Москва"
    assert data["street"] == "Тверская"
    assert data["raion"] is None
    assert data["city"] is None


async def test_create_registry_invalid_region(client: AsyncClient):
    response = await client.post(
        "/registries/",
        json={"region": "Атлантида", "street": "X"},
    )
    assert response.status_code == 422


async def test_create_registry_empty_street(client: AsyncClient):
    response = await client.post(
        "/registries/",
        json={"region": "Москва", "street": ""},
    )
    assert response.status_code == 422


# ============================================================
# READ (список)
# ============================================================

async def test_list_registries_empty(client: AsyncClient):
    response = await client.get("/registries/")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_registries(client: AsyncClient):
    await client.post(
        "/registries/",
        json={"region": "Москва", "street": "Тверская"},
    )
    await client.post(
        "/registries/",
        json={"region": "Московская область", "street": "Ленина"},
    )

    response = await client.get("/registries/")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_registries_pagination(client: AsyncClient):
    for i in range(5):
        await client.post(
            "/registries/",
            json={"region": "Москва", "street": f"Улица {i}"},
        )

    response = await client.get("/registries/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ============================================================
# READ (один)
# ============================================================

async def test_get_registry(client: AsyncClient):
    created = (
        await client.post(
            "/registries/",
            json={"region": "Москва", "street": "Тверская"},
        )
    ).json()

    response = await client.get(f"/registries/{created['id']}")
    assert response.status_code == 200
    assert response.json()["street"] == "Тверская"


async def test_get_registry_not_found(client: AsyncClient):
    response = await client.get("/registries/9999")
    assert response.status_code == 404


# ============================================================
# UPDATE
# ============================================================

async def test_update_registry(client: AsyncClient):
    created = (
        await client.post(
            "/registries/",
            json={"region": "Москва", "street": "Тверская"},
        )
    ).json()

    response = await client.patch(
        f"/registries/{created['id']}",
        json={"city": "Москва", "street": "Тверская-Ямская"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Москва"
    assert data["street"] == "Тверская-Ямская"
    assert data["updated_at"] is not None


async def test_update_registry_partial(client: AsyncClient):
    """PATCH одного поля не затирает остальные."""
    created = (
        await client.post(
            "/registries/",
            json={
                "region": "Москва",
                "raion": "Центральный",
                "city": "Москва",
                "street": "Тверская",
            },
        )
    ).json()

    updated = (
        await client.patch(
            f"/registries/{created['id']}",
            json={"street": "Новый Арбат"},
        )
    ).json()

    assert updated["region"] == "Москва"
    assert updated["raion"] == "Центральный"
    assert updated["city"] == "Москва"
    assert updated["street"] == "Новый Арбат"


async def test_update_registry_not_found(client: AsyncClient):
    response = await client.patch(
        "/registries/9999", json={"street": "X"}
    )
    assert response.status_code == 404


# ============================================================
# DELETE
# ============================================================

async def test_delete_registry(client: AsyncClient):
    created = (
        await client.post(
            "/registries/",
            json={"region": "Москва", "street": "Тверская"},
        )
    ).json()

    response = await client.delete(f"/registries/{created['id']}")
    assert response.status_code == 204

    response = await client.get(f"/registries/{created['id']}")
    assert response.status_code == 404


async def test_delete_registry_not_found(client: AsyncClient):
    response = await client.delete("/registries/9999")
    assert response.status_code == 404