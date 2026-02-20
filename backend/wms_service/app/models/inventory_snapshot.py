from decimal import Decimal
from sqlalchemy import Numeric, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase

class InventorySnapshot(MultiTenantBase):
    """
    Representa el stock actual valorizado.
    Fuente única de verdad para existencias y costo promedio (CPP).
    """
    __tablename__ = "inventory_snapshots"

    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), index=True)
    
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    
    # Bloqueo Optimista
    version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "product_id", "warehouse_id", name="uq_snapshot_company_product_warehouse"),
    )

    __mapper_args__ = {
        "version_id_col": version_id
    }