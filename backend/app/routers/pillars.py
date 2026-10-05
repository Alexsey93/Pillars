from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Pillar
from app.schemas import PillarCreate, PillarRead, PillarUpdate


router = APIRouter(prefix="/pillars", tags=["pillars"])


@router.post("/", response_model=PillarRead, status_code=status.HTTP_201_CREATED)
async def create_pillar(pillar: PillarCreate, session: SessionDep):
    db_pillar = Pillar.model_validate(pillar)
    session.add(db_pillar)
    await session.commit()
    await session.refresh(db_pillar)
    return db_pillar


@router.get("/", response_model=list[PillarRead])
async def list_pillars(session: SessionDep, skip: int = 0, limit: int = 20):
    statement = select(Pillar).offset(skip).limit(limit)
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
async def update_pillar(pillar_id: int, pillar: PillarUpdate, session: SessionDep):
    db_pillar = await session.get(Pillar, pillar_id)
    if db_pillar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar {pillar_id} not found",
        )
    update_data = pillar.model_dump(exclude_unset=True)
    db_pillar.sqlmodel_update(update_data)
    db_pillar.updated_at = datetime.now(timezone.utc)
    session.add(db_pillar)
    await session.commit()
    await session.refresh(db_pillar)
    return db_pillar


@router.delete("/{pillar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pillar(pillar_id: int, session: SessionDep):
    db_pillar = await session.get(Pillar, pillar_id)
    if db_pillar is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pillar {pillar_id} not found",
        )
    await session.delete(db_pillar)
    await session.commit()