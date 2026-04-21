import uuid
from sqlalchemy import String, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class BOM(MultiTenantBase):
    """
    Bill of Materials: Defines the relationship between a parent item 
    and its components for backflushing.
    Aligned with Legacy .NET BOM Model.
    """
    __tablename__ = "inventory_boms"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    component_item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=1.0)
    uom: Mapped[str] = mapped_column(String(20), nullable=False, default="PCS")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<BOM(parent='{self.parent_item_code}', component='{self.component_item_code}', qty={self.quantity}, level={self.level})>"
