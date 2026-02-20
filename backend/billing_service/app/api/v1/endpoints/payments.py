import uuid
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.billing import PaymentCreate, PaymentRead
from app.services.payment_service import PaymentService
from app.dependencies import get_current_user_payload, get_payment_service

router = APIRouter()


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def register_payment(
    data: PaymentCreate,
    user: dict = Depends(get_current_user_payload),
    svc: PaymentService = Depends(get_payment_service),
):
    """
    Registra un pago contra una factura.
    Actualiza automáticamente el estado de la factura (PARTIALLY_PAID / PAID).
    """
    company_id = uuid.UUID(user["company_id"])
    return await svc.register_payment(data, company_id)
