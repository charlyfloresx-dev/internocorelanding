"""
MaintenanceWorkOrder — Especialización CMMS de WorkOrderBase (DDD).

Hereda de common.WorkOrderBase que define el header compartido:
  folio, order_type, status, priority, priority_score,
  warehouse_id, source_ticket_id, assigned_to_id, etc.

Este modelo SOLO agrega campos específicos del dominio de Mantenimiento:
  - asset_id           → qué activo se interviene
  - maintenance_type   → Correctivo / Preventivo / Predictivo
  - maintenance_plan_id → plan que disparó la OT (si aplica)
  - tools_snapshot     → herramientas (INTERNAL_LOAN en Inventory)
  - consumables_snapshot → consumibles (PICK_AND_CONSUME en Inventory)
  - root_cause / resolution_notes → diagnóstico técnico
  - costos reales de mano de obra y refacciones
"""
import uuid
from decimal import Decimal
from typing import Optional, List, Any, TYPE_CHECKING

from sqlalchemy import String, Text, Numeric, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import WorkOrderBase, WorkOrderType
from cmms_app.core.constants import MaintenanceType

if TYPE_CHECKING:
    from .asset import Asset
    from .maintenance_plan import MaintenancePlan
    from .tool_assignment import ToolAssignment
    from .maintenance_evidence import MaintenanceEvidence


class MaintenanceWorkOrder(WorkOrderBase):
    """
    Orden de Trabajo de Mantenimiento.
    order_type siempre = WorkOrderType.MAINTENANCE (forzado en __init__).
    """
    __tablename__ = "cmms_work_orders"

    # ── Dominio específico: Mantenimiento ────────────────────────────────────
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_assets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    maintenance_plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_maintenance_plans.id", ondelete="SET NULL"), nullable=True
    )
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SAEnum(MaintenanceType), default=MaintenanceType.CORRECTIVE, nullable=False, index=True
    )

    # ── Diagnóstico técnico ──────────────────────────────────────────────────
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Costos reales ────────────────────────────────────────────────────────
    labor_cost_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    parts_cost_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    total_cost_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    cost_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # ── Herramientas — INTERNAL_LOAN en Inventory Service ───────────────────
    # [{"inventory_item_id": "uuid", "tool_id": "uuid", "name": "Llave Din."}]
    tools_snapshot: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # ── Consumibles — PICK_AND_CONSUME en Inventory Service ─────────────────
    # [{"inventory_item_id": "uuid", "name": "Lubricante 5W-30", "qty": 1, "uom": "L"}]
    consumables_snapshot: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    asset: Mapped["Asset"] = relationship("Asset", back_populates="work_orders")
    maintenance_plan: Mapped[Optional["MaintenancePlan"]] = relationship(
        "MaintenancePlan", back_populates="work_orders"
    )
    tool_assignments: Mapped[List["ToolAssignment"]] = relationship(
        "ToolAssignment", back_populates="work_order", cascade="all, delete-orphan"
    )
    evidence_files: Mapped[List["MaintenanceEvidence"]] = relationship(
        "MaintenanceEvidence", back_populates="work_order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_cmms_wo_company_status", "company_id", "status"),
        Index("ix_cmms_wo_company_asset", "company_id", "asset_id"),
        Index("ix_cmms_wo_scheduled", "company_id", "scheduled_start"),
    )

    def __init__(self, **kwargs):
        # Forzar el type correcto del Shared Kernel
        kwargs.setdefault("order_type", WorkOrderType.MAINTENANCE)
        super().__init__(**kwargs)
