from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.database import SessionDep
from app.models import Item
from app.schemas import ItemCreate, ItemRead, ItemUpdate


router = APIRouter(prefix="/items", tags=["items"])


# CREATE
@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate, session: SessionDep):
    db_item = Item.model_validate(item)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


# READ (список)
@router.get("/", response_model=list[ItemRead])
async def list_items(session: SessionDep, skip: int = 0, limit: int = 10):
    statement = select(Item).offset(skip).limit(limit)
    result = await session.execute(statement)
    return result.scalars().all()


# READ (один)
@router.get("/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, session: SessionDep):
    item = await session.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item


# UPDATE
@router.patch("/{item_id}", response_model=ItemRead)
async def update_item(item_id: int, item: ItemUpdate, session: SessionDep):
    db_item = await session.get(Item, item_id)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    update_data = item.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(update_data)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


# DELETE
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, session: SessionDep):
    db_item = await session.get(Item, item_id)
    if db_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    await session.delete(db_item)
    await session.commit()
