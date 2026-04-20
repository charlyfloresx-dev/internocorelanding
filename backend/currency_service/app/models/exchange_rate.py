import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Numeric, Boolean, DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


from common.models import MultiTenantBase

class CurrencyExchangeRate(MultiTenantBase):
    """
    Ledger inmutable de tipos de cambio.
    - Nunca se edita un registro, se crea uno nuevo.
    - is_suspicious: variación > umbral configurable (default 10%)
    - is_verified: en False hasta que un Admin lo apruebe (solo aplica si is_suspicious=True)
    - captured_by: NULL = worker automático, UUID = usuario manual
    """
    __tablename__ = "currency_exchange_rates"

    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="banxico", nullable=False)  # 'banxico' | 'frankfurter' | 'manual'
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    captured_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)


# Índice compuesto para lookups de reports: dame el rate más reciente y verificado
Index(
    "ix_cer_lookup",
    CurrencyExchangeRate.company_id,
    CurrencyExchangeRate.base_currency,
    CurrencyExchangeRate.target_currency,
    CurrencyExchangeRate.captured_at.desc(),
)
