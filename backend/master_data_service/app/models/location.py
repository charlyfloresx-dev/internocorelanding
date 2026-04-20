import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase

class InventoryLocation(MultiTenantBase):
    """
    [Phase 63] Master Data SSOT: Formal definition of a physical location in a warehouse.
    Now owned by Master Data Service to serve as the structural source of truth.
    """
    __tablename__ = "inventory_locations"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("warehouses.id", ondelete="CASCADE"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    # Capacity in units (PZA)
    max_capacity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0"))
    zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "warehouse_id", "code", name="uq_location_per_warehouse"),
    )

    def __repr__(self):
        return f"<InventoryLocation(code={self.code}, cap={self.max_capacity})>"
