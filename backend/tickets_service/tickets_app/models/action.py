from sqlalchemy import String, Text, DateTime, Boolean, UUID as sqlalchemy_UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase
import uuid
from typing import Optional
from datetime import datetime


class TicketAction(MultiTenantBase):
    __tablename__ = "ticket_actions"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), nullable=False)

    # Triple Identity — exactamente uno debe estar presente
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), nullable=True, index=True
    )  # Usuario digital
    collaborator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), nullable=True
    )  # Colaborador físico
    external_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), nullable=True
    )  # Contacto externo

    commit_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Fecha compromiso
    escalation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Límite antes de escalar
    closed_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Fecha de cierre real
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="actions")
