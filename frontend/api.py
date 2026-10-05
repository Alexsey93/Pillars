import requests
from typing import Optional
from models import Item


class ApiError(Exception):
    """Ошибка при обращении к API."""
    pass


class ItemsApi:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _handle(self, response: requests.Response) -> dict | list | None:
        if response.status_code == 204:
            return None
        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise ApiError(f"HTTP {response.status_code}: {detail}")
        return response.json()

    def list_items(self) -> list[Item]:
        r = requests.get(f"{self.base_url}/items/", timeout=self.timeout)
        data = self._handle(r)
        return [Item.from_dict(x) for x in data]

    def get_item(self, item_id: int) -> Item:
        r = requests.get(f"{self.base_url}/items/{item_id}", timeout=self.timeout)
        return Item.from_dict(self._handle(r))

    def create_item(self, name: str) -> Item:
        r = requests.post(
            f"{self.base_url}/items/",
            json={"name": name},
            timeout=self.timeout,
        )
        return Item.from_dict(self._handle(r))

    def update_item(self, item_id: int, name: str) -> Item:
        r = requests.patch(
            f"{self.base_url}/items/{item_id}",
            json={"name": name},
            timeout=self.timeout,
        )
        return Item.from_dict(self._handle(r))

    def delete_item(self, item_id: int) -> None:
        r = requests.delete(
            f"{self.base_url}/items/{item_id}",
            timeout=self.timeout,
        )
        self._handle(r)
