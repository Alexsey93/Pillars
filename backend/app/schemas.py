from sqlmodel import SQLModel, Field


class ItemCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)


class ItemUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class ItemRead(SQLModel):
    id: int
    name: str
