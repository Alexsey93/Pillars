from fastapi import HTTPException
from sqlmodel import select

from app.database import SessionDep
from app.models import Registry, User


async def get_accessible_registry(
    session: SessionDep,
    registry_id: int,
    user: User,
) -> Registry:
    """Возвращает реестр, если у пользователя есть к нему доступ.

    - Если реестр не найден — 404.
    - Если реестр чужой и пользователь не суперюзер — 403.
    """
    reg = await session.get(Registry, registry_id)
    if reg is None:
        raise HTTPException(status_code=404, detail="Registry not found")
    if not user.is_superuser and reg.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return reg