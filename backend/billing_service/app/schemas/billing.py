import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.enums import InvoiceStatus, CreditNoteType, PaymentMethod


# ─── PaymentTerm ────────────────────────────────────────────────
class PaymentTermBase(BaseModel):
    name: str
    days_due: int = 30
    discount_days: Optional[int] = None
    discount_percent: Optional[Decimal] = None
    is_active: bool = True

class PaymentTermCreate(PaymentTermBase):
    pass

class PaymentTermRead(PaymentTermBase):
    id: uuid.UUID
    company_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True


# ─── Invoice Item ────────────────────────────────────────────────
class InvoiceItemCreate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    sku: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("16")

class InvoiceItemRead(InvoiceItemCreate):
    id: uuid.UUID
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal

    class Config:
        from_attributes = True


# ─── Invoice ─────────────────────────────────────────────────────
class InvoiceCreate(BaseModel):
    customer_id: uuid.UUID
    customer_name: str
    customer_tax_id: Optional[str] = None
    series: Optional[str] = None
    payment_term_id: Optional[uuid.UUID] = None
    issue_date: datetime
    due_date: Optional[datetime] = None
    currency: str = "MXN"
    exchange_rate: Decimal = Decimal("1")
    notes: Optional[str] = None
    wms_document_id: Optional[uuid.UUID] = None
    items: List[InvoiceItemCreate]

class InvoiceRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    folio: str
    series: Optional[str]
    sequence_number: int
    customer_id: uuid.UUID
    customer_name: str
    customer_tax_id: Optional[str]
    status: InvoiceStatus
    issue_date: datetime
    due_date: Optional[datetime]
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str
    exchange_rate: Decimal
    notes: Optional[str]
    wms_document_id: Optional[uuid.UUID]
    items: List[InvoiceItemRead]

    class Config:
        from_attributes = True

class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


# ─── Credit Note ─────────────────────────────────────────────────
class CreditNoteCreate(BaseModel):
    invoice_id: uuid.UUID
    note_type: CreditNoteType
    amount: Decimal
    reason: Optional[str] = None
    issue_date: datetime

class CreditNoteRead(CreditNoteCreate):
    id: uuid.UUID
    company_id: uuid.UUID
    folio: str

    class Config:
        from_attributes = True


# ─── Payment ─────────────────────────────────────────────────────
class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    amount: Decimal
    payment_date: datetime
    method: PaymentMethod
    reference: Optional[str] = None
    notes: Optional[str] = None

class PaymentRead(PaymentCreate):
    id: uuid.UUID
    company_id: uuid.UUID

    class Config:
        from_attributes = True
