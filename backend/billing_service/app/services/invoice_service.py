import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.invoice import Invoice, InvoiceItem
from app.models.payment_term import PaymentTerm
from app.schemas.billing import InvoiceCreate
from app.core.enums import InvoiceStatus


class InvoiceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _next_sequence(self, company_id: uuid.UUID, series: str | None) -> int:
        """Genera el siguiente sequence_number para la combinación company+series."""
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.company_id == company_id)
            .where(Invoice.series == series)
            .order_by(Invoice.sequence_number.desc())
        )
        last = result.scalars().first()
        return (last.sequence_number + 1) if last else 1

    def _build_folio(self, series: str | None, sequence: int) -> str:
        prefix = f"{series}-" if series else ""
        return f"{prefix}{sequence:06d}"

    async def create_invoice(
        self, data: InvoiceCreate, company_id: uuid.UUID
    ) -> Invoice:
        seq = await self._next_sequence(company_id, data.series)
        folio = self._build_folio(data.series, seq)

        invoice = Invoice(
            company_id=company_id,
            folio=folio,
            series=data.series,
            sequence_number=seq,
            customer_id=data.customer_id,
            customer_name=data.customer_name,
            customer_tax_id=data.customer_tax_id,
            payment_term_id=data.payment_term_id,
            issue_date=data.issue_date,
            due_date=data.due_date,
            currency=data.currency,
            exchange_rate=data.exchange_rate,
            notes=data.notes,
            wms_document_id=data.wms_document_id,
            status=InvoiceStatus.DRAFT,
        )

        for item_data in data.items:
            item = InvoiceItem(
                company_id=company_id,
                product_id=item_data.product_id,
                sku=item_data.sku,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                discount_percent=item_data.discount_percent,
                tax_rate=item_data.tax_rate,
                subtotal=Decimal("0"),
                tax_amount=Decimal("0"),
                total=Decimal("0"),
            )
            item.compute()
            invoice.items.append(item)

        invoice.recalculate_totals()

        self.db.add(invoice)
        await self.db.flush()
        return invoice

    async def get_invoice(self, invoice_id: uuid.UUID, company_id: uuid.UUID) -> Invoice | None:
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.id == invoice_id, Invoice.company_id == company_id)
        )
        return result.scalars().first()

    async def list_invoices(
        self, company_id: uuid.UUID, status: InvoiceStatus | None = None
    ) -> list[Invoice]:
        q = select(Invoice).where(Invoice.company_id == company_id)
        if status:
            q = q.where(Invoice.status == status)
        result = await self.db.execute(q.order_by(Invoice.sequence_number.desc()))
        return list(result.scalars().all())

    async def update_status(
        self, invoice_id: uuid.UUID, company_id: uuid.UUID, new_status: InvoiceStatus
    ) -> Invoice | None:
        invoice = await self.get_invoice(invoice_id, company_id)
        if invoice:
            invoice.status = new_status
            await self.db.flush()
        return invoice
