import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Boolean, Numeric, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase

class PriceType(str, enum.Enum):
    LIST = "LIST"
    COST = "COST"
    TRANSFER = "TRANSFER"

class ProductPrice(MultiTenantBase):
    __tablename__ = "product_prices"

    product_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), index=True, nullable=True)
    
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), default=PriceType.LIST)
    
    # Valores Financieros (Numeric 18,4)
    purchase_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    # Incluido para paridad con WMS_CORE
    transfer_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())