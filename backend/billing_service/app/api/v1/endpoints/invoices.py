import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.billing import InvoiceCreate, InvoiceRead, InvoiceStatusUpdate
from app.services.invoice_service import InvoiceService
from app.core.enums import InvoiceStatus
from app.dependencies import get_current_user_payload, get_invoice_service

router = APIRouter()


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    user: dict = Depends(get_current_user_payload),
    svc: InvoiceService = Depends(get_invoice_service),
):
    """Crea una nueva factura en estado DRAFT."""
    company_id = uuid.UUID(user["company_id"])
    invoice = await svc.create_invoice(data, company_id)
    return invoice


@router.get("/", response_model=list[InvoiceRead])
async def list_invoices(
    status_filter: Optional[InvoiceStatus] = None,
    user: dict = Depends(get_current_user_payload),
    svc: InvoiceService = Depends(get_invoice_service),
):
    """Lista todas las facturas de la empresa, con filtro opcional por estado."""
    company_id = uuid.UUID(user["company_id"])
    return await svc.list_invoices(company_id, status=status_filter)


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: uuid.UUID,
    user: dict = Depends(get_current_user_payload),
    svc: InvoiceService = Depends(get_invoice_service),
):
    """Obtiene el detalle de una factura por ID."""
    company_id = uuid.UUID(user["company_id"])
    invoice = await svc.get_invoice(invoice_id, company_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return invoice


@router.patch("/{invoice_id}/status", response_model=InvoiceRead)
async def update_invoice_status(
    invoice_id: uuid.UUID,
    body: InvoiceStatusUpdate,
    user: dict = Depends(get_current_user_payload),
    svc: InvoiceService = Depends(get_invoice_service),
):
    """Actualiza el estado de una factura (ej. DRAFT → ISSUED → SENT)."""
    company_id = uuid.UUID(user["company_id"])
    invoice = await svc.update_status(invoice_id, company_id, body.status)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return invoice
