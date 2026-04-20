import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, UniqueConstraint, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from common.models import MultiTenantBase

from common.models import BaseProduct

class Item(BaseProduct):
    """
    Representa un artículo almacenable en WMS.
    Hereda el core (SKU/Name/Status) de Master Data pero añade logística local.
    """
    __tablename__ = "products"

    # Local logistics metadata
    stock_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0)
    bin_location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    master_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint('company_id', 'sku', name='uq_item_company_sku'),
    )