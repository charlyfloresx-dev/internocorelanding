from sqlalchemy import UUID as sqlalchemy_UUID, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase
import uuid
from decimal import Decimal

class TicketResource(MultiTenantBase):
    """
    Represents materials/parts consumed during the execution of a ticket.
    Maintains a weak reference to the inventory resource_id to prevent 
    hard coupling across microservices.
    """
    __tablename__ = "ticket_resources"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    # Weak reference to Master Data / Inventory Product UUID
    resource_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), index=True, nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    
    ticket: Mapped["Ticket"] = relationship("app.models.ticket.Ticket", back_populates="resources")
