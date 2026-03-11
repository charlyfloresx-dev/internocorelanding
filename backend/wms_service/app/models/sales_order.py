import enum
import uuid
from typing import Optional
from sqlalchemy import String, Integer, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase, Base

class SalesOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PICKED = "PICKED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

class SalesOrder(MultiTenantBase, Base):
    """
    Representa una Orden de Venta en el WMS.
    """
    __tablename__ = "sales_orders"

    folio: Mapped[str] = mapped_column(String(50), index=True, unique=True, nullable=False)
    
    status: Mapped[SalesOrderStatus] = mapped_column(
        Enum(SalesOrderStatus), 
        default=SalesOrderStatus.DRAFT,
        nullable=False
    )

    # Campos de Negocio para el Demo
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(15, 4), default=0.0)
    
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observations: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
