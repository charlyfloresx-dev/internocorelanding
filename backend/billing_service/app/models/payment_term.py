import uuid
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.domain import MultiTenantBase


class PaymentTerm(MultiTenantBase):
    """
    Términos de pago (ej. "30 días neto", "2/10 neto 30").
    company_id = NULL → término global del sistema.
    company_id = <uuid> → término personalizado de la empresa.
    """
    __tablename__ = "payment_terms"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    translation_key: Mapped[str] = mapped_column(String(100), nullable=True)

    days_due: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    discount_days: Mapped[int] = mapped_column(Integer, nullable=True)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
