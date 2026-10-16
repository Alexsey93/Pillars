from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from app.config import settings


# Создаем общий Base для SQLAlchemy
class Base(DeclarativeBase):
    pass


# Связываем SQLModel с SQLAlchemy
SQLModel.metadata = Base.metadata
SQLModel._sa_registry = Base.registry


engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=SQLModelAsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]