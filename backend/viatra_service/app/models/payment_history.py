import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase, AuditBase

class PaymentHistory(MultiTenantBase):
    __tablename__ = "viatra_payment_history"

    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("viatra_traveler_groups.id"), nullable=False)
    
    stripe_session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    status: Mapped[str] = mapped_column(String(50), nullable=False) # PAID, FAILED, REFUNDED
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
