from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Pillar, Registry
from app.schemas import PillarCreate, PillarRead, PillarUpdate
from app.users import current_active_user


router = APIRouter(
    prefix="/pillars",
    tags=["pillars"],
    dependencies=[Depends(current_active_user)],
)


async def _validate_registry(session: SessionDep, registry_id: int):
    reg = await session.get(Registry, registry_id)
    if reg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registry {registry_id} not found",
        )
    return reg


@router.post("/", response_model=PillarRead, status_code=status.HTTP_201_CREATED)
async def create_pillar(data: PillarCreate, session: SessionDep):
    await _validate_registry(session, data.registry_id)
    db_pillar = Pillar.model_validate(data)
    session.add(db_pillar)
    await session.commit()
    await session.refresh(db_pillar)
    return db_pillar


@router.get("/", response_model=list[PillarRead])
async def list_pillars(
    session: SessionDep,
    registry_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    statement = select(Pillar)
    if registry_id is not None:
        statement = statement.where(Pillar.registry_id == registry_id)
    statement = statement.offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()


@router.get("/{pillar_id}", response_model=PillarRead)
async def get_pillar(pillar_id: int, session: SessionDep):
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar {pillar_id} not found",
        )
    return pillar


@router.patch("/{pillar_id}", response_model=PillarRead)
async def update_pillar(pillar_id: int, data: PillarUpdate, session: SessionDep):
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar {pillar_id} not found",
        )
    update_data = data.model_dump(exclude_unset=True)
    if "registry_id" in update_data:
        await _validate_registry(session, update_data["registry_id"])
    pillar.sqlmodel_update(update_data)
    pillar.updated_at = datetime.now(timezone.utc)
    session.add(pillar)
    await session.commit()
    await session.refresh(pillar)
    return pillar


@router.delete("/{pillar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pillar(pillar_id: int, session: SessionDep):
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar {pillar_id} not found",
        )
    await session.delete(pillar)
    await session.commit()