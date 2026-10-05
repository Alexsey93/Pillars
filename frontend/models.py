from dataclasses import dataclass
from typing import Optional


@dataclass
class Item:
    id: int
    name: str

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(id=data["id"], name=data["name"])


@dataclass
class ItemCreate:
    name: str


@dataclass
class ItemUpdate:
    name: Optional[str] = None
