import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, DateTime, Boolean, ForeignKey, Integer, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from common.domain import MultiTenantBase
from app.core.enums import InvoiceStatus


class Invoice(MultiTenantBase):
    """
    Documento de factura. Triple Identity Pattern:
      - folio (visible, por empresa)
      - series + sequence_number (folio fiscal)
    """
    __tablename__ = "invoices"

    folio: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    series: Mapped[str] = mapped_column(String(20), nullable=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Datos del cliente (snapshot para preservar histórico)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_tax_id: Mapped[str] = mapped_column(String(50), nullable=True)

    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT
    )

    payment_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_terms.id"), nullable=True
    )
    payment_term = relationship("PaymentTerm")

    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Totales financieros
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MXN")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False, default=1)

    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Referencia cruzada con WMS (opcional)
    wms_document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    credit_notes = relationship("CreditNote", back_populates="invoice")
    payments = relationship("Payment", back_populates="invoice")

    __table_args__ = (
        UniqueConstraint('folio', 'company_id', name='_company_folio_uc'),
        UniqueConstraint('series', 'sequence_number', 'company_id', name='_company_series_seq_uc'),
    )

    def recalculate_totals(self) -> None:
        """Recalcula subtotal, tax_amount y total a partir de los ítems."""
        self.subtotal = sum(i.subtotal for i in self.items)
        self.tax_amount = sum(i.tax_amount for i in self.items)
        self.total = self.subtotal + self.tax_amount - self.discount_amount


class InvoiceItem(MultiTenantBase):
    """Línea de detalle de factura."""
    __tablename__ = "invoice_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    invoice = relationship("Invoice", back_populates="items")

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("16"))

    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    def compute(self) -> None:
        """Calcula montos del ítem a partir de precio y cantidad."""
        base = self.quantity * self.unit_price
        discount = base * (self.discount_percent / Decimal("100"))
        self.subtotal = base - discount
        self.tax_amount = self.subtotal * (self.tax_rate / Decimal("100"))
        self.total = self.subtotal + self.tax_amount
