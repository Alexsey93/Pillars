import httpx
from models import Pillar


class ApiError(Exception):
    """Ошибка при обращении к API."""
    pass


class PillarsApi:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Возвращает единый AsyncClient, создаёт при необходимости."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Закрывает HTTP-клиент. Вызывается при завершении приложения."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _handle(self, response: httpx.Response):
        """Разбирает ответ. Бросает ApiError при ошибке."""
        if response.status_code == 204:
            return None
        if not response.is_success:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(f"HTTP {response.status_code}: {detail}")
        return response.json()

    async def list_pillars(self, skip: int = 0, limit: int = 50) -> list[Pillar]:
        client = await self._get_client()
        r = await client.get(
            f"{self.base_url}/pillars/",
            params={"skip": skip, "limit": limit},
        )
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