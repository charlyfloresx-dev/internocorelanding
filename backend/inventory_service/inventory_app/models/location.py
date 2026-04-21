import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase

try:
    from master_app.models.location import InventoryLocation
    _REUSED_LOCATION = True
except (ImportError, Exception):
    _REUSED_LOCATION = False

if not _REUSED_LOCATION:
    class InventoryLocation(MultiTenantBase):
        """
        Formal definition of a physical location in a warehouse (Rack, Bin, Section).
        Used for 'The Density Guard' capacity validation.
        """
        __tablename__ = "inventory_locations"
    
        warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
        code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
        
        # Capacity in units (PZA) or weight/volume if we want more complexity.
        # We'll start with piece-based capacity.
        max_capacity: Mapped[Decimal] = mapped_column(Numeric(15, 4), default=Decimal("0.0"))
        zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
        __table_args__ = (
            UniqueConstraint("company_id", "warehouse_id", "code", name="uq_location_per_warehouse"),
            {"extend_existing": True},
        )
    
        def __repr__(self):
            return f"<InventoryLocation(code={self.code}, cap={self.max_capacity})>"
