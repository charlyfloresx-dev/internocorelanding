import uuid
from typing import Optional, List
from pydantic import BaseModel
from app.domain.enums import PhotoStatus


# ─── Request Schemas ───────────────────────────────────────────────────────────

class RequestUploadUrlIn(BaseModel):
    """Guest asks for a presigned URL before uploading directly to MinIO."""
    event_id: uuid.UUID
    company_id: uuid.UUID
    guest_session_id: str
    guest_name: Optional[str] = None
    filename: str
    content_type: str = "image/jpeg"
    file_size_bytes: Optional[int] = None


class ApprovePhotosIn(BaseModel):
    """Novios approve or reject a batch of photos (swipe Tinder style)."""
    approvals: List[dict]   # [{"photo_id": UUID, "approved": bool}]


# ─── Response Schemas ──────────────────────────────────────────────────────────

class UploadUrlOut(BaseModel):
    photo_id: uuid.UUID
    upload_url: str         # Presigned PUT → client uploads directly to MinIO
    object_key: str
    expires_in: int = 300


class ReviewPhotoIn(BaseModel):
    approver_index: int
    device_id: str
    action: str    # "APPROVE" or "REJECT"

class PhotoOut(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    company_id: uuid.UUID
    guest_name: Optional[str]
    status: PhotoStatus
    url: Optional[str] = None
    thumb_url: Optional[str] = None
    mime_type: str
    file_size_bytes: Optional[int]
    approval_count: int
    required_approvals: Optional[int] = None

    class Config:
        from_attributes = True
