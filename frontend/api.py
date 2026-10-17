import httpx

from auth import auth_state
from models import Pillar, Registry


class ApiError(Exception):
    pass


class PillarsApi:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=auth_state.headers(),
            )
        return self._client

    async def reset_client(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    def _handle(self, response: httpx.Response):
        if response.status_code == 204:
            return None
        if not response.is_success:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(f"HTTP {response.status_code}: {detail}")
        return response.json()

    # REGISTRIES

    async def list_registries(self, skip: int = 0, limit: int = 100) -> list[Registry]:
        client = await self._get_client()
        r = await client.get(
            f"{self.base_url}/registries/",
            params={"skip": skip, "limit": limit},
        )
        return [Registry.from_dict(x) for x in self._handle(r)]

    async def get_registry(self, registry_id: int) -> Registry:
        client = await self._get_client()
        r = await client.get(f"{self.base_url}/registries/{registry_id}")
        return Registry.from_dict(self._handle(r))

    async def create_registry(self, data: dict) -> Registry:
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/registries/", json=data)
        return Registry.from_dict(self._handle(r))

    async def update_registry(self, registry_id: int, data: dict) -> Registry:
        client = await self._get_client()
        r = await client.patch(
            f"{self.base_url}/registries/{registry_id}", json=data
        )
        return Registry.from_dict(self._handle(r))

    async def delete_registry(self, registry_id: int) -> None:
        client = await self._get_client()
        r = await client.delete(f"{self.base_url}/registries/{registry_id}")
        self._handle(r)

    # PILLARS

    async def list_pillars(
        self, registry_id: int | None = None, skip: int = 0, limit: int = 100
    ) -> list[Pillar]:
        client = await self._get_client()
        params = {"skip": skip, "limit": limit}
        if registry_id is not None:
            params["registry_id"] = registry_id
        r = await client.get(f"{self.base_url}/pillars/", params=params)
        return [Pillar.from_dict(x) for x in self._handle(r)]

    async def get_pillar(self, pillar_id: int) -> Pillar:
        client = await self._get_client()
        r = await client.get(f"{self.base_url}/pillars/{pillar_id}")
        return Pillar.from_dict(self._handle(r))

    async def create_pillar(self, data: dict) -> Pillar:
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/pillars/", json=data)
        return Pillar.from_dict(self._handle(r))

    async def update_pillar(self, pillar_id: int, data: dict) -> Pillar:
        client = await self._get_client()
        r = await client.patch(
            f"{self.base_url}/pillars/{pillar_id}", json=data
        )
        return Pillar.from_dict(self._handle(r))

    async def delete_pillar(self, pillar_id: int) -> None:
        client = await self._get_client()
        r = await client.delete(f"{self.base_url}/pillars/{pillar_id}")
        self._handle(r)

    # EXPORT

    async def get_download_link(self, registry_id: int) -> str:
        """Запрашивает у бэкенда одноразовую ссылку для скачивания."""
        client = await self._get_client()
        r = await client.post(f"{self.base_url}/export/registry/{registry_id}/link")
        data = self._handle(r)
        return data["url"]