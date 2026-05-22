from sqlalchemy import String, Text, Integer, DateTime, Enum as sqlalchemy_Enum, UUID as sqlalchemy_UUID, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase
from tickets_app.core.constants import TicketStatus, TicketPriority, TicketType
import uuid
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class Ticket(MultiTenantBase):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("company_id", "reference_code", name="tickets_company_id_reference_code_key"),
    )

    reference_code: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    ticket_type: Mapped[TicketType] = mapped_column(
        sqlalchemy_Enum(TicketType, values_callable=lambda e: [m.value for m in e]), default=TicketType.SUPPORT, index=True
    )
    priority: Mapped[TicketPriority] = mapped_column(
        sqlalchemy_Enum(TicketPriority, values_callable=lambda e: [m.value for m in e]), default=TicketPriority.MEDIUM, index=True
    )
    status: Mapped[TicketStatus] = mapped_column(
        sqlalchemy_Enum(TicketStatus, values_callable=lambda e: [m.value for m in e]), default=TicketStatus.NEW, index=True
    )
    
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), index=True, nullable=True
    ) # ID del Usuario del sistema (Identidad Digital)

    collaborator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), index=True, nullable=True
    ) # ID del Colaborador industrial (Identidad Física)

    external_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), index=True, nullable=True
    ) # ID del Contacto Externo (Proveedor)

    assigned_department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), index=True, nullable=True
    ) # ID del Departamento asignado (Asignación flexible a departamento)

    external_assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    ) # Fecha de asignación externa para SLA de 72h
    
    # Anti-Fatigue Debouncing
    deduplication_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    
    external_token: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True) # Token para acceso externo
    
    # MES/ERP Execution metrics
    module_origin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # e.g., PRODUCTION, INVENTORY
    area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estimated_time: Mapped[Optional[int]] = mapped_column(nullable=True) # in minutes
    real_time_spent: Mapped[Optional[int]] = mapped_column(nullable=True) # in minutes
    cost_estimate: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True)
    
    # --- Fase 5: Campos Operacionales Industriales ---
    source_service: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # Origen: "INVENTORY", "MES", "MANUAL", "SENSOR"

    station_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), nullable=True, index=True
    )  # Weak ref a MES station (para Mantenimiento y Tiempo Muerto)

    reported_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), nullable=True
    )  # ID del usuario que reportó (para notificaciones de cierre)

    parent_ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        sqlalchemy_UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True
    )  # Para escalación: ticket hijo referencia al padre

    auto_close_on_event: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Evento de cierre automático: "KARDEX_ENTRY_CONFIRMED"

    escalation_level: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )  # 0 = sin escalar, 1 = jefe turno, 2 = gerente área, 3 = gerente planta

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Para cálculo de MTTR (Mean Time To Repair)

    # Relationships
    comments: Mapped[List["TicketComment"]] = relationship(
        "TicketComment", back_populates="ticket", cascade="all, delete-orphan"
    )
    history: Mapped[List["TicketHistory"]] = relationship(
        "TicketHistory", back_populates="ticket", cascade="all, delete-orphan"
    )
    resources: Mapped[List["TicketResource"]] = relationship(
        "TicketResource", back_populates="ticket", cascade="all, delete-orphan"
    )
    stop_logs: Mapped[List["StopLog"]] = relationship(
        "StopLog", back_populates="ticket", cascade="all, delete-orphan",
        foreign_keys="StopLog.ticket_id"
    )
    # Self-referential: tickets de escalación apuntando al ticket padre
    child_tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket", back_populates="parent_ticket", cascade="all",
        foreign_keys="Ticket.parent_ticket_id"
    )
    parent_ticket: Mapped[Optional["Ticket"]] = relationship(
        "Ticket", back_populates="child_tickets", remote_side="Ticket.id",
        foreign_keys="Ticket.parent_ticket_id"
    )
