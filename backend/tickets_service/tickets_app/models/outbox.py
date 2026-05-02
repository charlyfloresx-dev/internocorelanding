from sqlalchemy import String, Text, Boolean, DateTime, UUID as sqlalchemy_UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase
import uuid
from datetime import datetime
from typing import Optional

class OutboxEvent(MultiTenantBase):
    """
    Implements the Transactional Outbox Pattern.
    Events are saved in the same transaction as the domain entities,
    ensuring guaranteed delivery to the Notification Service or other consumers.
    """
    __tablename__ = "outbox_events"

    event_id: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), default=uuid.uuid4, index=True, unique=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    
    # JSON serialized TicketCreatedEvent or similar event payload
    payload: Mapped[str] = mapped_column(Text)
    
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

