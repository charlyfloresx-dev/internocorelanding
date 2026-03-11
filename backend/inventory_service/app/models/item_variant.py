import uuid
from decimal import Decimal
from sqlalchemy import String, Numeric, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase

class ItemVariant(MultiTenantBase):
    """
    Cross-reference table for Item Variants (Brand equivalents).
    Allows searching by Manufacturer Part Number (MPN).
    """
    __tablename__ = "inventory_item_variants"

    # Pattern borrowed from inventory.py
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    internal_sku: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    mfg_part_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0.0"))
    
    # Industrial attributes
    weight: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True) # kg
    volume: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=True) # m3
    
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("company_id", "internal_sku", "mfg_part_number", name="uq_variant_per_company"),
    )

    def __repr__(self):
        return f"<ItemVariant(sku='{self.internal_sku}', brand='{self.brand}', mpn='{self.mfg_part_number}')>"
