import uuid
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.payment import Payment
from app.models.invoice import Invoice
from app.schemas.billing import PaymentCreate
from app.core.enums import InvoiceStatus


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_payment(
        self, data: PaymentCreate, company_id: uuid.UUID
    ) -> Payment:
        payment = Payment(
            company_id=company_id,
            invoice_id=data.invoice_id,
            amount=data.amount,
            payment_date=data.payment_date,
            method=data.method,
            reference=data.reference,
            notes=data.notes,
        )
        self.db.add(payment)
        await self.db.flush()

        # Actualizar estatus de la factura
        await self._update_invoice_status(data.invoice_id, company_id)
        return payment

    async def _update_invoice_status(
        self, invoice_id: uuid.UUID, company_id: uuid.UUID
    ) -> None:
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id, Invoice.company_id == company_id
            )
        )
        invoice = result.scalars().first()
        if not invoice:
            return

        payments_result = await self.db.execute(
            select(Payment).where(Payment.invoice_id == invoice_id)
        )
        payments = payments_result.scalars().all()
        total_paid = sum(p.amount for p in payments)

        if total_paid >= invoice.total:
            invoice.status = InvoiceStatus.PAID
        elif total_paid > Decimal("0"):
            invoice.status = InvoiceStatus.PARTIALLY_PAID

        await self.db.flush()
