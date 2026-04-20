import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from common.models import MultiTenantBase, AuditBase

class PriceAlert(MultiTenantBase):
    __tablename__ = "viatra_price_alerts"

    package_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("viatra_travel_packages.id"), nullable=False)
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("viatra_traveler_groups.id"), nullable=True)
    
    flight_number: Mapped[str] = mapped_column(String(20), nullable=False)
    
    old_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False) # FLIGHT_DROP, HOTEL_DROP
    is_processed: Mapped[bool] = mapped_column(default=False)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
