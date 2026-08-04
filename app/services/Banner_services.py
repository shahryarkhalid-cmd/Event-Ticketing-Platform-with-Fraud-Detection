import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from core.supabase_client import supabase
from models.Users import User 
from sqlmodel import Session
from services.User_services import get_current_user
from database import get_session
from models.Event import Event
BUCKET_NAME = "event_banners"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 5

async def upload_event_banner_service(
    event_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    if event.organizer_id != current_user.id:
        raise HTTPException(403, "You don't own this event")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, or WEBP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large. Max {MAX_SIZE_MB}MB")

    ext = file.filename.split(".")[-1].lower()
    storage_path = f"{event_id}/{uuid.uuid4().hex}.{ext}"

    if event.banner_storage_path:
        try:
            supabase.storage.from_(BUCKET_NAME).remove([event.banner_storage_path])
        except Exception:
            pass

    supabase.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=contents,
        file_options={"content-type": file.content_type, "upsert": "true"},
    )
    banner_url = supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)

    event.banner_url = banner_url
    event.banner_storage_path = storage_path
    session.add(event)
    session.flush()
    session.refresh(event)

    return {"banner_url": banner_url}