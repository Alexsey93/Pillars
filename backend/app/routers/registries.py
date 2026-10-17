from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Registry, User
from app.schemas import RegistryCreate, RegistryRead, RegistryUpdate
from app.users import current_active_user


router = APIRouter(
    prefix="/registries",
    tags=["registries"],
)


def _can_access(user: User, registry: Registry) -> bool:
    """Проверяет, имеет ли пользователь доступ к реестру."""
    return user.is_superuser or registry.owner_id == user.id


@router.post("/", response_model=RegistryRead, status_code=status.HTTP_201_CREATED)
async def create_registry(
    data: RegistryCreate,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    # Создаем объект Registry вручную, передавая owner_id
    db_reg = Registry(
        owner_id=user.id,
        region=data.region,
        raion=data.raion,
        city=data.city,
        street=data.street,
    )
    session.add(db_reg)
    await session.commit()
    await session.refresh(db_reg)
    return db_reg


@router.get("/", response_model=list[RegistryRead])
async def list_registries(
    session: SessionDep,
    user: User = Depends(current_active_user),
    skip: int = 0,
    limit: int = 100,
):
    statement = select(Registry)

    # Если не админ — показываем только свои реестры
    if not user.is_superuser:
        statement = statement.where(Registry.owner_id == user.id)

    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/{registry_id}", response_model=RegistryRead)
async def get_registry(
    registry_id: int,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    reg = await session.get(Registry, registry_id)
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registry {registry_id} not found",
        )
    if not _can_access(user, reg):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return reg


@router.patch("/{registry_id}", response_model=RegistryRead)
async def update_registry(
    registry_id: int,
    data: RegistryUpdate,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    reg = await session.get(Registry, registry_id)
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registry {registry_id} not found",
        )
    if not _can_access(user, reg):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    update_data = data.model_dump(exclude_unset=True)
    reg.sqlmodel_update(update_data)
    reg.updated_at = datetime.now(timezone.utc)
    session.add(reg)
    await session.commit()
    await session.refresh(reg)
    return reg


@router.delete("/{registry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_registry(
    registry_id: int,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    reg = await session.get(Registry, registry_id)
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registry {registry_id} not found",
        )
    if not _can_access(user, reg):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    await session.delete(reg)
    await session.commit()