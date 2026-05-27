from sqlalchemy import String, Boolean, DateTime, UUID as sqlalchemy_UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase
from sqlalchemy import func
import uuid
from datetime import datetime
from typing import Optional


class TicketAssignee(MultiTenantBase):
    __tablename__ = "ticket_assignees"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # INTERNAL | PLANTA | EXTERNO
    identity_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), nullable=False, index=True
    )
    is_lead: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), nullable=True
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="assignees")
