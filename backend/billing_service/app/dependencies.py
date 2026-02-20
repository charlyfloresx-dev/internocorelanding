from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.services.invoice_service import InvoiceService
from app.services.payment_service import PaymentService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user_payload(token: Annotated[str, Depends(oauth2_scheme)]) -> dict:
    """
    Valida el JWT y extrae el contexto multitenant.
    TODO: Reemplazar el mock por `common.security.decode_access_token(token)`
    """
    # Mock para estructura — reemplazar con lógica de common.security
    payload = {"sub": "user_id", "company_id": "uuid-company"}

    company_id = payload.get("company_id")
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company context in token. Multitenancy violation.",
        )
    return payload


# ─── Service Factories ────────────────────────────────────────────
async def get_invoice_service(db: AsyncSession = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db)


async def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


# Alias
get_current_user = get_current_user_payload
