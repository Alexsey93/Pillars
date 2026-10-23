import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlmodel import select

from app.config import settings
from app.database import SessionDep
from app.models import Pillar, User
from app.users import current_active_user

router = APIRouter(
    prefix="/pillars",
    tags=["photos"],
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/{pillar_id}/photo", status_code=status.HTTP_201_CREATED)
async def upload_pillar_photo(
    pillar_id: int,
    session: SessionDep,
    user: User = Depends(current_active_user),
    file: UploadFile = File(...),
):
    """Загружает фото для опоры."""
    # 1. Проверяем, что опора существует и доступна пользователю
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail="Pillar not found")

    # Здесь можно добавить проверку прав (как в pillars.py)
    # registry = await session.get(Registry, pillar.registry_id)
    # if not user.is_superuser and registry.owner_id != user.id:
    #     raise HTTPException(status_code=403, detail="Access denied")

    # 2. Проверяем расширение файла
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый формат файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # 3. Генерируем уникальное имя файла, чтобы не перезаписывать
    # (используем переданное имя как базу, но добавляем UUID для уникальности)
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in (" ", "-", "_", ".")).strip()
    unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    file_path = os.path.join(settings.upload_dir, unique_filename)

    # 4. Сохраняем файл
    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # 5. Возвращаем URL для доступа (относительный)
    file_url = f"/uploads/{unique_filename}"
    
    return {"url": file_url, "filename": unique_filename}


@router.get("/photo/{filename}")
async def get_pillar_photo(filename: str):
    """Отдает сохраненное фото."""
    # Защита от path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(settings.upload_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)