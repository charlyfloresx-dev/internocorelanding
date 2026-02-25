from sqlalchemy import String, Text, UUID as sqlalchemy_UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.domain.entities import MultiTenantBase
import uuid

class TicketComment(MultiTenantBase):
    __tablename__ = "ticket_comments"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), nullable=False)
    
    # Relationships
    ticket: Mapped["app.models.ticket.Ticket"] = relationship("app.models.ticket.Ticket", back_populates="comments")
