import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import Base
from datetime import datetime

class PhotoApproval(Base):
    __tablename__ = "photo_approvals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    photo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("event_photos.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_index: Mapped[int] = mapped_column(Integer, nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("photo_id", "approver_index", name="uq_photo_approver_index"),
        UniqueConstraint("photo_id", "device_id", name="uq_photo_device_id"),
    )
