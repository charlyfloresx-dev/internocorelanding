"""
WorkOrderBase — Entidad abstracta compartida del dominio (DDD Shared Kernel).

DISEÑO: La Orden de Trabajo es un concepto transversal a múltiples contextos
acotados (Bounded Contexts) dentro de Interno Core:
  - CMMS      → MaintenanceWorkOrder  (asset, técnico, herramientas)
  - MES       → ProductionWorkOrder   (BOM, rutas, estación)
  - WMS       → KittingWorkOrder      (pick list, staging, despacho)
  - Tickets   → (origen del trigger, puede escalar a Maintenance)

Esta clase base define el "WorkOrderHeader" compartido per el SSOT.
Cada servicio hereda de ella con __abstract__ = True para mantener
tablas físicamente separadas (sin FK cross-service) y evitar duplicación.

Referencia del SSOT:
  - Folio único legible: WO-2026-A4K2
  - priority_score: calculado (1-100) por el Priority Engine
  - warehouse_id: ubicación física de la ejecución (weak-ref)
  - source_ticket_id: escalación Ticket → WorkOrder (weak-ref)
"""
import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

from common.infrastructure.models.base import MultiTenantBase


# ─────────────────────────────────────────────
# ENUMS GLOBALES (compartidos por todos los servicios)
# ─────────────────────────────────────────────

class WorkOrderType(str, enum.Enum):
    MAINTENANCE = "MAINTENANCE"   # CMMS
    PRODUCTION = "PRODUCTION"     # MES
    KITTING = "KITTING"           # WMS
    RECEIPT = "RECEIPT"           # Inbound Logistics
    QUALITY = "QUALITY"           # QC / Inspección


class WorkOrderBaseStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class WorkOrderBasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ─────────────────────────────────────────────
# BASE ABSTRACT MODEL
# ─────────────────────────────────────────────

class WorkOrderBase(MultiTenantBase):
    """
    Clase base abstracta para todas las Órdenes de Trabajo de Interno Core.

    INSTRUCCIONES DE HERENCIA:
      1. Heredar en el servicio destino.
      2. Definir __tablename__ en la clase hija.
      3. NO agregar FK directas a otras tablas de otros servicios
         (usar weak-refs UUID para mantener aislamiento de servicios).

    EJEMPLO:
      class MaintenanceWorkOrder(WorkOrderBase):
          __tablename__ = "cmms_work_orders"
          asset_id: Mapped[uuid.UUID] = ...   # dominio específico
    """
    __abstract__ = True

    # ── Identificación legible ────────────────────────────────────────────────
    folio: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    order_type: Mapped[WorkOrderType] = mapped_column(
        SAEnum(WorkOrderType), nullable=False, index=True
    )

    # ── Estado y prioridad unificados ─────────────────────────────────────────
    status: Mapped[WorkOrderBaseStatus] = mapped_column(
        SAEnum(WorkOrderBaseStatus), default=WorkOrderBaseStatus.OPEN, nullable=False, index=True
    )
    priority: Mapped[WorkOrderBasePriority] = mapped_column(
        SAEnum(WorkOrderBasePriority), default=WorkOrderBasePriority.MEDIUM, nullable=False, index=True
    )
    # Valor calculado por el Priority Engine (1-100).
    # Formula: (C × Severity) + (W × (1 / DaysToDueDate))
    priority_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # ── Ubicación física de la ejecución (weak-ref al WMS) ───────────────────
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # ── Descripción ───────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # ── Escalación / origen (weak-ref cross-service) ──────────────────────────
    # Ticket que originó esta orden (ej. Ticket de falla → MaintenanceWorkOrder)
    source_ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # ── Asignación (weak-ref a HCM) ───────────────────────────────────────────
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    supervisor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    reported_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # ── Fechas UTC ────────────────────────────────────────────────────────────
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    scheduled_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
