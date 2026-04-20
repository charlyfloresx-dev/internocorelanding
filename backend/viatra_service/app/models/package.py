import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Numeric, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, composite


from common.models import MultiTenantBase, AuditBase
from common.value_objects import Money

class TravelPackage(MultiTenantBase):
    __tablename__ = "viatra_travel_packages"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    destination: Mapped[str] = mapped_column(String(100), nullable=False)

    _amount: Mapped[Decimal] = mapped_column("total_price_amount", Numeric(18, 4), server_default="0", default=0)
    _currency: Mapped[str] = mapped_column("total_price_currency", String(3), server_default="USD", default="USD")
    total_price: Mapped[Money] = composite(Money, _amount, _currency)

    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Fintech Integration
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Sentinel Thresholds
    target_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)


