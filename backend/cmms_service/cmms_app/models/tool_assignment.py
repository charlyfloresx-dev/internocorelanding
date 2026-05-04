"""ToolAssignment — Check-out / Check-in de herramientas vinculado a una WorkOrder."""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Text, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import MultiTenantBase
from cmms_app.core.constants import ToolCondition

if TYPE_CHECKING:
    from .tool import Tool
    from .work_order import MaintenanceWorkOrder


class ToolAssignment(MultiTenantBase):
    """
    Registro de préstamo de herramienta vinculado a una WorkOrder.
    Invariante: una WorkOrder con estado COMPLETED no puede tener
    ToolAssignments donde returned_at sea NULL.
    """
    __tablename__ = "cmms_tool_assignments"

    tool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_tools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # ── Timestamps UTC ───────────────────────────────────────────────────────
    checked_out_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_return_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Condición de entrega / retorno ───────────────────────────────────────
    checkout_condition: Mapped[ToolCondition] = mapped_column(SAEnum(ToolCondition), nullable=False)
    return_condition: Mapped[Optional[ToolCondition]] = mapped_column(SAEnum(ToolCondition), nullable=True)
    return_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Firma digital del vale de resguardo ───────────────────────────────────
    signature_file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    tool: Mapped["Tool"] = relationship("Tool", back_populates="assignments")
    work_order: Mapped["MaintenanceWorkOrder"] = relationship("MaintenanceWorkOrder", back_populates="tool_assignments")

    __table_args__ = (
        Index("ix_cmms_tool_assign_company_tool", "company_id", "tool_id"),
        Index("ix_cmms_tool_assign_company_wo", "company_id", "work_order_id"),
    )
