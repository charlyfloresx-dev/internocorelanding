import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, UUID as sqlalchemy_UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class ProcessedEvent(MultiTenantBase):
    """
    Log of processed event IDs to ensure idempotency across the service.
    """
    __tablename__ = "notif_processed_events"

    # We keep event_id as the business/event identifier, 
    # but id (from MultiTenantBase) is the technical PK.
    event_id: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), index=True, unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ProcessedEvent(id={self.event_id}, type={self.event_type})>"
