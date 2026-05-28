import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase
from mes_app.core.enums import WOType

if TYPE_CHECKING:
    from .work_order_line import WorkOrderLine


class WorkOrder(MultiTenantBase):
    """Orden de Trabajo MES (Documento cabecera)."""
    __tablename__ = "mes_work_orders"

    # ERP order number (source system reference)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    item_code: Mapped[str] = mapped_column(String(100), index=True)

    order_quantity: Mapped[int] = mapped_column(Integer)
    manufactured_quantity: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(50), default="DRAFT")
    material_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # MES-specific classification (NON_STANDARD, STANDARD, REPAIR, REWORK…)
    wo_type: Mapped[Optional[WOType]] = mapped_column(
        SAEnum(WOType, name="wotype"), nullable=True, index=True
    )

    # Routing (weak-ref to mes_routings; nullable until Rout model is implemented)
    rout_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    alias: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    request_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Document pattern: one-to-many lines (BOM explode + output)
    lines: Mapped[list["WorkOrderLine"]] = relationship(
        "WorkOrderLine",
        back_populates="work_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
