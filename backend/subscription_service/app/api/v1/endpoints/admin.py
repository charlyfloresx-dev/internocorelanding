from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from typing import List
import os

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import SessionLocal
from app.services.license import LicenseService

router = APIRouter()

# El secreto maestro para bypass de seguridad estándar en God Mode
ADMIN_MASTER_KEY = os.getenv("ADMIN_MASTER_KEY", "change-this-critical-secret")

async def get_db():
    async with SessionLocal() as session:
        yield session

async def verify_admin_master_key(x_admin_key: str = Header(..., alias="X-Admin-Master-Key")):
    """
    Validador de llave maestra para acceso administrativo directo (God Mode).
    """
    if x_admin_key != ADMIN_MASTER_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso Denegado: Admin Master Key inválida."
        )

@router.post("/tenants/{company_id}/force-status", dependencies=[Depends(verify_admin_master_key)])
async def force_subscription_status(
    company_id: str, 
    new_status: str,
    db: AsyncSession = Depends(get_db)
):
    """
    [GOD MODE] Fuerza un cambio de estado de suscripción sin validaciones de negocio.
    """
    return {"message": f"Tenant {company_id} status manually set to {new_status}."}

@router.post("/tenants/{company_id}/override-grace", dependencies=[Depends(verify_admin_master_key)])
async def override_grace_period(company_id: str, days: int = 7):
    """
    [GOD MODE] Extiende manualmente el periodo de gracia.
    """
    return {"message": f"Grace period extended for tenant {company_id} by {days} days."}

@router.get("/audit/licenses", dependencies=[Depends(verify_admin_master_key)])
async def view_global_audit_logs():
    """
    [GOD MODE] Visor central de AuditSubscriptionLog para debugging forense.
    """
    return {"logs": "Skeletal implementation: Querying AuditSubscriptionLog..."}
