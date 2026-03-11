import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Boolean, Numeric, Enum, DateTime, func, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase, AuditBase

class PriceType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    TRANSFER = "TRANSFER"
    COST = "COST"

class PriceOriginType(str, enum.Enum):
    MANUAL = "MANUAL"
    BULK = "BULK"
    AUTO = "AUTO"           # Calculated by system
    SEED = "SEED"           # Initial data

class ProductPrice(MultiTenantBase, AuditBase):
    __tablename__ = "product_prices"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    channel_code: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), default=PriceType.SALE, nullable=False)
    
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=0)
    
    currency_code: Mapped[str] = mapped_column(String(3), server_default="USD", default="USD")
    
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    change_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    
    origin_type: Mapped[PriceOriginType] = mapped_column(Enum(PriceOriginType), default=PriceOriginType.MANUAL)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", default=True)