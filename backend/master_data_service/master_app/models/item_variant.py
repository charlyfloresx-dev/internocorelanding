import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase


class ItemVariant(MultiTenantBase):
    """
    Cross-reference table for Item Variants (Brand / Supplier equivalents).
    Lives in master_data_db — treated as master catalog data.
    Allows typeahead search by Manufacturer Part Number (MPN) or internal SKU.
    """
    __tablename__ = "inventory_item_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    internal_sku: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    mfg_part_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0.0"))
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "internal_sku", "mfg_part_number", name="uq_variant_per_company"),
    )
