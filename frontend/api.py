import requests
from models import Pillar


class ApiError(Exception):
    pass


class PillarsApi:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _handle(self, response: requests.Response):
        if response.status_code == 204:
            return None
        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(f"HTTP {response.status_code}: {detail}")
        return response.json()

    def list_pillars(self, skip: int = 0, limit: int = 50) -> list[Pillar]:
        r = requests.get(
            f"{self.base_url}/pillars/",
            params={"skip": skip, "limit": limit},
            timeout=self.timeout,
        )
        return [Pillar.from_dict(x) for x in self._handle(r)]

    def get_pillar(self, pillar_id: int) -> Pillar:
        r = requests.get(
            f"{self.base_url}/pillars/{pillar_id}", timeout=self.timeout
        )
        return Pillar.from_dict(self._handle(r))

    def create_pillar(self, data: dict) -> Pillar:
        r = requests.post(
            f"{self.base_url}/pillars/", json=data, timeout=self.timeout
        )
        return Pillar.from_dict(self._handle(r))

    def update_pillar(self, pillar_id: int, data: dict) -> Pillar:
        r = requests.patch(
            f"{self.base_url}/pillars/{pillar_id}",
            json=data,
            timeout=self.timeout,
        )
        return Pillar.from_dict(self._handle(r))

    def delete_pillar(self, pillar_id: int) -> None:
        r = requests.delete(
            f"{self.base_url}/pillars/{pillar_id}", timeout=self.timeout
        )
        self._handle(r)