import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Numeric, Boolean, DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import Base, MultiTenantBase

# DEPRECATED: Use the dedicated currency-service instead of local exchange rates.
# Moving towards microservice-based currency management [2026-04-05]
class CurrencyExchangeRate(MultiTenantBase):
    """
    Local cache/storage of exchange rates.
    @deprecated: Transitioning to CurrencyExchangeService API.
    """
    __tablename__ = "currency_exchange_rates"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    captured_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

# Índice compuesto para lookups
Index(
    "ix_mds_cer_lookup",
    CurrencyExchangeRate.company_id,
    CurrencyExchangeRate.base_currency,
    CurrencyExchangeRate.target_currency,
    CurrencyExchangeRate.captured_at.desc(),
)
