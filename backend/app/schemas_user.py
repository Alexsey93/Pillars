import uuid
from typing import Optional

from fastapi_users import schemas
from pydantic import Field


class UserRead(schemas.BaseUser[uuid.UUID]):
    email: str


class UserCreate(schemas.BaseUserCreate):
    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=128)
    invite_code: str = Field(min_length=1, max_length=100)   # ← новое поле


class UserUpdate(schemas.BaseUserUpdate):
    email: Optional[str] = Field(default=None, min_length=3, max_length=100)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)