import uuid
from decimal import Decimal
from sqlalchemy import Numeric, ForeignKey, String, UniqueConstraint, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class Stock(MultiTenantBase):
    """
    Representation of current stock for a product in a warehouse.
    Must be reconciled with Movement Ledger.
    """
    __tablename__ = "inventory_stocks"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    # 🔒 Ledger Alignment: quantity should reflect the sum of all movements
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    
    # Industrial Control Fields
    min_stock: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0) # Safety Stock
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)

    @property
    def available_quantity(self) -> Decimal:
        """SSOT Calculation: Available = Total - Reserved"""
        return self.quantity - self.reserved_quantity

    __table_args__ = (
        UniqueConstraint('warehouse_id', 'product_id', 'company_id', name='uq_warehouse_product_tenant'),
    )

    def __repr__(self):
        return f"<Stock(warehouse={self.warehouse_id}, product={self.product_id}, qty={self.quantity})>"
