import uuid
from typing import Optional
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase

class ProductionSession(MultiTenantBase):
    __tablename__ = "production_sessions"

    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    current_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="IDLE") # ACTIVE, PAUSED, STOPPED
    
    last_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<ProductionSession(resource={self.resource_id}, status={self.status})>"
