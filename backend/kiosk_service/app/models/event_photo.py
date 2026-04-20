import uuid
from sqlalchemy import String, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import AuditBase
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.payment_order import PaymentOrder


from app.domain.enums import PhotoStatus


class EventPhoto(AuditBase):
    __tablename__ = "event_photos"

    # Tenant / Event identifiers
    company_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)

    # Uploader info (guest – no FK to avoid coupling)
    guest_session_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    guest_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Storage
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)      # MinIO key
    thumb_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False, default="image/jpeg")
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    status: Mapped[PhotoStatus] = mapped_column(
        SAEnum(PhotoStatus, name="photo_status"),
        nullable=False,
        default=PhotoStatus.UPLOADED,
        index=True,
    )

    # Quórum Approval
    approval_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    payment_orders: Mapped[List["PaymentOrder"]] = relationship(
        "PaymentOrder", back_populates="photo", cascade="all, delete-orphan"
    )
