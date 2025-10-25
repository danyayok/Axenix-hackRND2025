from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories.room_repo import RoomRepository
from app.repositories.recording_repo import RecordingRepository
from app.repositories.membership_repo import MembershipRepository
from app.services.recording import RecordingService

router = APIRouter()

def _svc(db: AsyncSession) -> RecordingService:
    return RecordingService(RoomRepository(db), MembershipRepository(db), RecordingRepository(db))

@router.post("/{room_slug}/upload")
async def upload_record(
    room_slug: str,
    uploader_user_id: int,
    title: str = Form("Recording"),
    duration_sec: int | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await _svc(db).save_file(
            room_slug=room_slug,
            uploader_user_id=uploader_user_id,
            filename=file.filename,
            file_obj=file.file,
            title=title,
            duration_sec=duration_sec,
        )
    except PermissionError:
        raise HTTPException(HTTP_403_FORBIDDEN, "Forbidden")
    except ValueError as e:
        raise HTTPException(HTTP_404_NOT_FOUND, str(e))

@router.get("/{room_slug}")
async def list_records(room_slug: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    try:
        return {"items": await _svc(db).list(room_slug=room_slug, limit=limit)}
    except ValueError as e:
        raise HTTPException(HTTP_404_NOT_FOUND, str(e))

@router.delete("/{room_slug}/{rec_id}")
async def delete_record(room_slug: str, rec_id: int, actor_user_id: int, db: AsyncSession = Depends(get_db)):
    svc = _svc(db)
    try:
        ok = await svc.delete(room_slug=room_slug, rec_id=rec_id, actor_user_id=actor_user_id)
        return {"ok": ok}
    except PermissionError:
        raise HTTPException(HTTP_403_FORBIDDEN, "Forbidden")
    except ValueError as e:
        raise HTTPException(HTTP_404_NOT_FOUND, str(e))
