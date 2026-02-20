import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy import String, Text, Numeric, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from common.domain import MultiTenantBase
from app.core.enums import CreditNoteType


class CreditNote(MultiTenantBase):
    """
    Nota de crédito aplicada contra una factura.
    Reduce el saldo pendiente de la factura referenciada.
    """
    __tablename__ = "credit_notes"

    folio: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False
    )
    invoice = relationship("Invoice", back_populates="credit_notes")

    note_type: Mapped[CreditNoteType] = mapped_column(
        Enum(CreditNoteType), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint('folio', 'company_id', name='_cn_company_folio_uc'),
    )
