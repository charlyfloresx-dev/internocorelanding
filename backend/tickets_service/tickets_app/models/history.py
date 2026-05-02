from sqlalchemy import String, UUID as sqlalchemy_UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase, AuditBase
import uuid
from typing import Optional

class TicketHistory(MultiTenantBase):
    __tablename__ = "ticket_history"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # status_change, priority_change, assignment_change
    old_value: Mapped[Optional[str]] = mapped_column(String(100))
    new_value: Mapped[Optional[str]] = mapped_column(String(100))
    changed_by_id: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), nullable=False)
    
    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="history")
