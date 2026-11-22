from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.database import SessionDep
from app.deps import get_accessible_registry as _get_accessible_registry
from app.models import Pillar, User
from app.schemas import PillarCreate, PillarRead, PillarUpdate
from app.users import current_active_user

router = APIRouter(prefix="/pillars", tags=["pillars"])


@router.post("/", response_model=PillarRead, status_code=status.HTTP_201_CREATED)
async def create_pillar(
    data: PillarCreate,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    await _get_accessible_registry(session, data.registry_id, user)

    db_pillar = Pillar.model_validate(data)
    session.add(db_pillar)
    await session.commit()
    await session.refresh(db_pillar)

    # Вычисляем номер для ответа
    stmt = select(func.count(Pillar.id)).where(Pillar.registry_id == data.registry_id)
    result = await session.execute(stmt)
    count = result.scalar_one()

    pydantic_pillar = PillarRead.model_validate(db_pillar)
    pydantic_pillar.number_in_registry = count
    return pydantic_pillar


@router.get("/", response_model=list[PillarRead])
async def list_pillars(
    session: SessionDep,
    user: User = Depends(current_active_user),
    registry_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
):
    # Используем ROW_NUMBER() для плотной нумерации
    stmt = select(
        Pillar,
        func.row_number().over(
            partition_by=Pillar.registry_id,
            order_by=Pillar.id
        ).label("calc_number")
    )

    if registry_id is not None:
        await _get_accessible_registry(session, registry_id, user)
        stmt = stmt.where(Pillar.registry_id == registry_id)
    else:
        if not user.is_superuser:
            from app.models import Registry
            reg_stmt = select(Registry.id).where(Registry.owner_id == user.id)
            reg_result = await session.execute(reg_stmt)
            allowed_ids = reg_result.scalars().all()
            if not allowed_ids:
                return []
            stmt = stmt.where(Pillar.registry_id.in_(allowed_ids))

    stmt = stmt.order_by(Pillar.id).offset(skip).limit(limit)
    result = await session.execute(stmt)

    response = []
    for row in result.all():
        pillar = row[0]
        calc_number = row[1]

        pydantic_pillar = PillarRead.model_validate(pillar)
        pydantic_pillar.number_in_registry = calc_number
        response.append(pydantic_pillar)

    return response


@router.get("/{pillar_id}", response_model=PillarRead)
async def get_pillar(
    pillar_id: int,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail=f"Pillar {pillar_id} not found")

    await _get_accessible_registry(session, pillar.registry_id, user)

    stmt = select(func.count(Pillar.id)).where(
        Pillar.registry_id == pillar.registry_id,
        Pillar.id <= pillar.id
    )
    result = await session.execute(stmt)
    calc_number = result.scalar_one()

    pydantic_pillar = PillarRead.model_validate(pillar)
    pydantic_pillar.number_in_registry = calc_number
    return pydantic_pillar


@router.patch("/{pillar_id}", response_model=PillarRead)
async def update_pillar(
    pillar_id: int,
    data: PillarUpdate,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail=f"Pillar {pillar_id} not found")

    await _get_accessible_registry(session, pillar.registry_id, user)

    update_data = data.model_dump(exclude_unset=True)
    if "registry_id" in update_data:
        await _get_accessible_registry(session, update_data["registry_id"], user)

    pillar.sqlmodel_update(update_data)
    pillar.updated_at = datetime.now(timezone.utc)
    session.add(pillar)
    await session.commit()
    await session.refresh(pillar)

    stmt = select(func.count(Pillar.id)).where(
        Pillar.registry_id == pillar.registry_id,
        Pillar.id <= pillar.id
    )
    result = await session.execute(stmt)
    calc_number = result.scalar_one()

    pydantic_pillar = PillarRead.model_validate(pillar)
    pydantic_pillar.number_in_registry = calc_number
    return pydantic_pillar


@router.delete("/{pillar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pillar(
    pillar_id: int,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail=f"Pillar {pillar_id} not found")

    await _get_accessible_registry(session, pillar.registry_id, user)

    await session.delete(pillar)
    await session.commit()