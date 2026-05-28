import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Numeric, UniqueConstraint, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase
from mes_app.core.enums import WorkOrderLineType, WorkOrderLineStatus

if TYPE_CHECKING:
    from .work_order import WorkOrder


class WorkOrderLine(MultiTenantBase):
    """
    Línea de Orden de Trabajo — Patrón Documento+Líneas.

    MATERIAL_INPUT  → componente consumido (explode del BOM)
    PLANNED_OUTPUT  → pieza terminada planeada
    SCRAP           → desperdicio controlado

    actual_quantity se actualiza en tiempo real por ScannerService al escanear
    piezas terminadas (PLANNED_OUTPUT) o en backflush de materiales (MATERIAL_INPUT).
    """
    __tablename__ = "mes_work_order_lines"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mes_work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    line_type: Mapped[WorkOrderLineType] = mapped_column(
        SAEnum(WorkOrderLineType, name="workorderlinetype"), nullable=False, index=True
    )

    item_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    item_description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    actual_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    uom: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    status: Mapped[WorkOrderLineStatus] = mapped_column(
        SAEnum(WorkOrderLineStatus, name="workorderlinestatus"),
        default=WorkOrderLineStatus.PENDING,
        nullable=False,
    )

    # Weak-ref to inventory BOM record (no cross-service FK)
    bom_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    work_order: Mapped["WorkOrder"] = relationship(
        "WorkOrder",
        back_populates="lines",
        lazy="noload",
    )

    __table_args__ = (
        UniqueConstraint("work_order_id", "line_number", name="uq_wo_line_number"),
    )
