import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.storage import generate_presigned_upload_url, get_object_stream
from app.models.event_photo import EventPhoto, PhotoStatus
from app.models.event import Event
from app.models.photo_approval import PhotoApproval
from app.schemas.photo import RequestUploadUrlIn, UploadUrlOut, PhotoOut, ApprovePhotosIn, ReviewPhotoIn

router = APIRouter()

@router.post("/upload-url", response_model=UploadUrlOut)
async def request_upload_url(payload: RequestUploadUrlIn, db: AsyncSession = Depends(get_db)):
    """
    Called by the Guest app. Returns a presigned URL to upload directly to MinIO.
    This avoids passing large image bytes through FastAPI, ensuring speed on the local network.
    """
    photo_id = uuid.uuid4()
    # E.g. events/{event_id}/{photo_id}.jpg
    object_key = f"events/{payload.event_id}/{photo_id}_{payload.filename}"

    # 1. Generate Presigned URL
    url = generate_presigned_upload_url(object_key, payload.content_type)

    # 2. Track in DB with UPLOADED status (or DONE for videos to skip approval)
    status = PhotoStatus.DONE if payload.content_type.startswith('video/') else PhotoStatus.UPLOADED

    photo = EventPhoto(
        id=photo_id,
        event_id=payload.event_id,
        company_id=payload.company_id,
        guest_session_id=payload.guest_session_id,
        guest_name=payload.guest_name,
        object_key=object_key,
        mime_type=payload.content_type,
        file_size_bytes=payload.file_size_bytes,
        status=status,
    )
    db.add(photo)
    await db.commit()

    return UploadUrlOut(
        photo_id=photo_id,
        upload_url=url,
        object_key=object_key,
        expires_in=300
    )


@router.get("/gallery/{event_id}", response_model=List[PhotoOut])
async def get_gallery(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns all APPROVED photos for the public gallery.
    """
    result = await db.execute(
        select(EventPhoto, Event.required_approvals)
        .join(Event, EventPhoto.event_id == Event.id)
        .where(
            EventPhoto.event_id == event_id,
            EventPhoto.status == PhotoStatus.APPROVED
        ).order_by(EventPhoto.created_at.desc())
    )
    photos_data = result.all()
    
    # Generate secure proxy URLs
    out_photos = []
    for p, req_app in photos_data:
        p_out = PhotoOut.model_validate(p)
        # Using secure domain proxy for full SSL compatibility
        p_out.url = f"/api/v1/kiosk/photos/serve/{p.id}"
        p_out.required_approvals = req_app
        out_photos.append(p_out)
    return out_photos


@router.get("/pending-approval/{event_id}", response_model=List[PhotoOut])
async def get_pending_photos(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Returns all UPLOADED photos for the Novios' Tinder-style swipe app.
    Requires Staff/Admin Auth (omitted here for brevity).
    """
    result = await db.execute(
        select(EventPhoto, Event.required_approvals)
        .join(Event, EventPhoto.event_id == Event.id)
        .where(
            EventPhoto.event_id == event_id,
            EventPhoto.status == PhotoStatus.UPLOADED
        ).order_by(EventPhoto.created_at.asc())
    )
    photos_data = result.all()
    
    out_photos = []
    for p, req_app in photos_data:
        p_out = PhotoOut.model_validate(p)
        p_out.url = f"/api/v1/kiosk/photos/serve/{p.id}"
        p_out.required_approvals = req_app
        out_photos.append(p_out)
    return out_photos


@router.post("/{photo_id}/review")
async def review_photo(photo_id: uuid.UUID, payload: ReviewPhotoIn, db: AsyncSession = Depends(get_db)):
    """
    Generalized N-Approver mechanism. 
    Tracks approvals per role and per device to ensure quórum.
    """
    photo = await db.get(EventPhoto, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    event = await db.get(Event, photo.event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if payload.action == "REJECT":
        photo.status = PhotoStatus.REJECTED
        await db.commit()
        return {"status": "ok", "photo_state": photo.status}

    if payload.action == "APPROVE":
        # 1. Validate index
        if payload.approver_index < 1 or payload.approver_index > event.required_approvals:
            raise HTTPException(status_code=400, detail=f"Invalid approver index. Max is {event.required_approvals}")

        # 2. Check if this role already approved this photo
        existing_role = await db.execute(
            select(PhotoApproval).where(
                PhotoApproval.photo_id == photo_id,
                PhotoApproval.approver_index == payload.approver_index
            )
        )
        if existing_role.scalars().first():
             # Already approved by this index, skip duplication but return current state
             return {"status": "ok", "photo_state": photo.status, "approval_count": photo.approval_count}

        # 3. Check if this DEVICE already approved this photo (prevent one person doing multiple roles)
        existing_device = await db.execute(
            select(PhotoApproval).where(
                PhotoApproval.photo_id == photo_id,
                PhotoApproval.device_id == payload.device_id
            )
        )
        if existing_device.scalars().first():
             raise HTTPException(status_code=403, detail="Este dispositivo ya ha aprobado esta foto")

        # 4. Register Approval
        new_approval = PhotoApproval(
            photo_id=photo_id,
            approver_index=payload.approver_index,
            device_id=payload.device_id
        )
        db.add(new_approval)
        
        # 5. Atomically update count
        photo.approval_count += 1
        
        # 6. Check Quórum
        if photo.approval_count >= event.required_approvals:
            photo.status = PhotoStatus.APPROVED
            
        await db.commit()
        await db.refresh(photo)
        
        return {
            "status": "ok", 
            "photo_state": photo.status, 
            "approval_count": photo.approval_count,
            "required_approvals": event.required_approvals
        }
    
    return {"status": "error", "message": "Invalid action"}


@router.post("/{photo_id}/reset-approvals")
async def reset_photo_approvals(photo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Staff Emergency Reset.
    Clears all approvals for a photo and resets its count and status.
    """
    from sqlalchemy import delete
    photo = await db.get(EventPhoto, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    # 1. Delete all approval records
    await db.execute(delete(PhotoApproval).where(PhotoApproval.photo_id == photo_id))
    
    # 2. Reset photo state
    photo.approval_count = 0
    photo.status = PhotoStatus.UPLOADED
    
    await db.commit()
    return {"status": "ok", "message": "Quórum reiniciado"}


@router.get("/serve/{photo_id}")
async def serve_photo(photo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Secure Proxy to serve MinIO images through the same HTTPS port.
    Prevents Mixed Content and port accessibility issues on mobiles.
    """
    photo = await db.get(EventPhoto, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    stream, content_type = get_object_stream(photo.object_key)
    return StreamingResponse(stream, media_type=content_type)
