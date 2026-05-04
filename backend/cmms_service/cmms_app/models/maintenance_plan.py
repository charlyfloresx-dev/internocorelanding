"""MaintenancePlan — Definición de mantenimiento recurrente (Preventivo/Predictivo)."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, Boolean, Numeric, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import MultiTenantBase
from cmms_app.core.constants import MaintenanceType, MaintenanceFrequencyUnit

if TYPE_CHECKING:
    from .asset import Asset
    from .work_order import MaintenanceWorkOrder


class MaintenancePlan(MultiTenantBase):
    """
    Define la lógica de recurrencia de un mantenimiento preventivo.
    Un activo puede tener múltiples planes activos simultáneamente
    (ej: cambio de aceite cada 30 días + revisión eléctrica cada 6 meses).
    """
    __tablename__ = "cmms_maintenance_plans"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        SAEnum(MaintenanceType), default=MaintenanceType.PREVENTIVE, nullable=False, index=True
    )

    # ── Frecuencia ───────────────────────────────────────────────────────────
    frequency_value: Mapped[int] = mapped_column(Integer, nullable=False)
    frequency_unit: Mapped[MaintenanceFrequencyUnit] = mapped_column(
        SAEnum(MaintenanceFrequencyUnit), default=MaintenanceFrequencyUnit.DAYS, nullable=False
    )

    # ── Tracking de ejecución ────────────────────────────────────────────────
    last_execution_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_execution_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Estimaciones económicas ──────────────────────────────────────────────
    estimated_cost_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    estimated_cost_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    estimated_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Herramientas requeridas (snapshot JSONB) ─────────────────────────────
    # [{"tool_id": "uuid", "name": "Llave Dinamométrica"}]
    required_tools_snapshot: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ────────────────────────────────────────────────────────
    asset: Mapped["Asset"] = relationship("Asset", back_populates="maintenance_plans")
    work_orders: Mapped[List["MaintenanceWorkOrder"]] = relationship("MaintenanceWorkOrder", back_populates="maintenance_plan")

    __table_args__ = (
        Index("ix_cmms_plans_company_asset", "company_id", "asset_id"),
        Index("ix_cmms_plans_next_execution", "company_id", "next_execution_date"),
    )
