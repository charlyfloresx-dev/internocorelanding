import uuid
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import AuditBase
from typing import Optional

class Event(AuditBase):
    __tablename__ = "kiosk_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    photo_price: Mapped[int] = mapped_column(Integer, nullable=False, default=5000) # cents
    rule_paparazzi: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    watermark_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    required_approvals: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
