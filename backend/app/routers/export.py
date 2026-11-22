from io import BytesIO
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import update
from sqlmodel import select

from app.database import SessionDep
from app.deps import get_accessible_registry
from app.models import Registry, Pillar, DownloadToken, User
from app.schemas import DownloadLinkResponse
from app.users import current_active_user
from app.excel_export import generate_excel_bytes


router = APIRouter(prefix="/export", tags=["export"])


@router.post("/registry/{registry_id}/link", response_model=DownloadLinkResponse)
async def create_download_link(
    registry_id: int,
    session: SessionDep,
    user: User = Depends(current_active_user),
):
    """Создает одноразовую ссылку для скачивания реестра."""
    # Проверка доступа: реестр существует и принадлежит пользователю (или он суперюзер)
    await get_accessible_registry(session, registry_id, user)

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    db_token = DownloadToken(
        token=token,
        registry_id=registry_id,
        user_id=user.id,
        expires_at=expires_at,
    )
    session.add(db_token)
    await session.commit()

    return DownloadLinkResponse(url=f"/export/download/{token}")


@router.get("/download/{token}")
async def download_by_token(token: str, session: SessionDep):
    """Скачивает файл по одноразовому токену.

    Атомарно "сжигает" токен через UPDATE ... WHERE used=False AND expires_at > now.
    Это защищает от гонки: два параллельных запроса не смогут оба получить файл.
    """
    now = datetime.now(timezone.utc)

    stmt = (
        update(DownloadToken)
        .where(
            DownloadToken.token == token,
            DownloadToken.used == False,  # noqa: E712
            DownloadToken.expires_at > now,
        )
        .values(used=True)
        .returning(DownloadToken)
    )
    result = await session.execute(stmt)
    db_token = result.scalar_one_or_none()
    await session.commit()

    if db_token is None:
        # Различаем "не существует", "уже использован" и "просрочен" для UX
        exists_stmt = select(DownloadToken).where(DownloadToken.token == token)
        exists_result = await session.execute(exists_stmt)
        existing = exists_result.scalar_one_or_none()

        if existing is None:
            raise HTTPException(status_code=404, detail="Invalid token")
        if existing.used:
            raise HTTPException(status_code=400, detail="Token already used")
        if existing.expires_at <= now:
            raise HTTPException(status_code=400, detail="Token expired")
        raise HTTPException(status_code=400, detail="Token unavailable")

    registry = await session.get(Registry, db_token.registry_id)
    if registry is None:
        raise HTTPException(status_code=410, detail="Registry no longer exists")

    pillars_stmt = select(Pillar).where(Pillar.registry_id == db_token.registry_id)
    pillars_result = await session.execute(pillars_stmt)
    pillars = pillars_result.scalars().all()

    excel_bytes = generate_excel_bytes(pillars, registry)

    safe_street = "".join(c for c in registry.street if c.isalnum() or c in (" ", "-", "_")).strip()
    filename = f"Реестр_{safe_street}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )