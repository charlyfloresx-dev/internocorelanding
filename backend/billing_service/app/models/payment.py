import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Text, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from common.domain import MultiTenantBase
from app.core.enums import PaymentMethod


class Payment(MultiTenantBase):
    """
    Registro de pago aplicado a una factura.
    Un solo invoice puede tener múltiples payments (pagos parciales).
    """
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False
    )
    invoice = relationship("Invoice", back_populates="payments")

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    reference: Mapped[str] = mapped_column(String(255), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
