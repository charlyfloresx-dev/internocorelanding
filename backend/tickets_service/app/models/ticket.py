from sqlalchemy import String, Text, Enum as sqlalchemy_Enum, UUID as sqlalchemy_UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.domain.entities import MultiTenantBase
from app.core.constants import TicketStatus, TicketPriority, TicketType
import uuid
from typing import List, Optional

class Ticket(MultiTenantBase):
    __tablename__ = "tickets"

    reference_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    ticket_type: Mapped[TicketType] = mapped_column(
        sqlalchemy_Enum(TicketType), default=TicketType.SUPPORT, index=True
    )
    priority: Mapped[TicketPriority] = mapped_column(
        sqlalchemy_Enum(TicketPriority), default=TicketPriority.MEDIUM, index=True
    )
    status: Mapped[TicketStatus] = mapped_column(
        sqlalchemy_Enum(TicketStatus), default=TicketStatus.NEW, index=True
    )
    
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), index=True, nullable=True
    )
    
    # Relationships
    comments: Mapped[List["TicketComment"]] = relationship(
        "app.models.comments.TicketComment", back_populates="ticket", cascade="all, delete-orphan"
    )
    history: Mapped[List["TicketHistory"]] = relationship(
        "app.models.history.TicketHistory", back_populates="ticket", cascade="all, delete-orphan"
    )
