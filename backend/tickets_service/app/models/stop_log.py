from sqlalchemy import UUID as sqlalchemy_UUID, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase
import uuid

class StopLog(MultiTenantBase):
    """
    Represents production downtime associated with a ticket.
    Maintains a weak reference to the MES station_id.
    """
    __tablename__ = "ticket_stop_logs"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True
    )
    # Weak reference to MES Station UUID
    station_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), index=True, nullable=False
    )
    downtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    ticket: Mapped["Ticket"] = relationship("app.models.ticket.Ticket", back_populates="stop_logs")
