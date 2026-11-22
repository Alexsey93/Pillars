import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlmodel import select

from app.config import settings
from app.database import SessionDep
from app.deps import get_accessible_registry
from app.models import Pillar, User
from app.users import current_active_user

router = APIRouter(prefix="/pillars", tags=["photos"])
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/{pillar_id}/photo", status_code=status.HTTP_201_CREATED)
async def upload_pillar_photo(
    pillar_id: int,
    session: SessionDep,
    user: User = Depends(current_active_user),
    file: UploadFile = File(...),
):
    pillar = await session.get(Pillar, pillar_id)
    if pillar is None:
        raise HTTPException(status_code=404, detail="Pillar not found")

    await get_accessible_registry(session, pillar.registry_id, user)

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file format")

    safe_name = "".join(c for c in file.filename if c.isalnum() or c in (" ", "-", "_", ".")).strip()
    unique_filename = f"{uuid.uuid4().hex[:8]}_{safe_name}"
    file_path = os.path.join(settings.upload_dir, unique_filename)

    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    file_url = f"/pillars/photo/{unique_filename}"
    pillar.photo_url = file_url
    pillar.updated_at = datetime.now(timezone.utc)
    session.add(pillar)
    await session.commit()

    return {"url": file_url, "filename": unique_filename}


@router.get("/photo/{filename}")
async def get_pillar_photo(filename: str):
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(settings.upload_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)