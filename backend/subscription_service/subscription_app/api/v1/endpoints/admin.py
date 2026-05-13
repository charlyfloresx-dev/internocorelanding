from fastapi import APIRouter, Depends, HTTPException, Header, status, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List
import uuid

from subscription_app.dependencies.repositories import get_subscription_repository
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository
from subscription_app.core.enums import SubscriptionStatus
from common.config import settings
# Assuming StorageAuditService also needs refactoring but keeping it for now if it's out of scope or will be handled later
from subscription_app.infrastructure.storage_audit import StorageAuditService 
from subscription_app.application.change_subscription_plan_handler import ChangeSubscriptionPlanHandler, ChangeSubscriptionPlanCommand

class ChangePlanRequest(BaseModel):
    new_plan_id: str
    reason: str = "Admin plan change"

router = APIRouter()


async def verify_admin_master_key(x_admin_key: str = Header(..., alias="X-Admin-Master-Key")):
    if not settings or not settings.int_admin_master_key or x_admin_key != settings.int_admin_master_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso Denegado: Admin Master Key inválida o no configurada."
        )


@router.post("/tenants/{company_id}/force-activate", dependencies=[Depends(verify_admin_master_key)])
async def force_activate_tenant(
    company_id: uuid.UUID, 
    request: Request,
    repo: ISubscriptionRepository = Depends(get_subscription_repository)
):
    """
    [GOD MODE] Fuerza la activación de una suscripción omitiendo validaciones de pago.
    """
    transaction_id = getattr(request.state, "transaction_id", str(uuid.uuid4()))
    
    sub = await repo.get_subscription_by_company(company_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    await repo.update_subscription_status(company_id, SubscriptionStatus.ACTIVE)

    return {
        "status": "success",
        "message": f"Tenant {company_id} activado manualmente via God Mode.",
        "transaction_id": transaction_id
    }


@router.post("/tenants/{company_id}/force-status", dependencies=[Depends(verify_admin_master_key)])
async def force_subscription_status(
    company_id: uuid.UUID, 
    new_status: SubscriptionStatus,
    request: Request,
    repo: ISubscriptionRepository = Depends(get_subscription_repository)
):
    await repo.update_subscription_status(company_id, new_status)
    return {"message": f"Tenant {company_id} status manually set to {new_status}."}


@router.post("/tenants/{company_id}/override-grace", dependencies=[Depends(verify_admin_master_key)])
async def override_grace_period(
    company_id: uuid.UUID, 
    days: int = 7,
    repo: ISubscriptionRepository = Depends(get_subscription_repository)
):
    sub = await repo.extend_grace_period(company_id, days)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    return {
        "status": "success",
        "message": f"Grace period extended until {sub.grace_period_until} for tenant {company_id}."
    }

from sqlalchemy.ext.asyncio import AsyncSession
from subscription_app.dependencies import get_db

@router.post("/tenants/{company_id}/change-plan", dependencies=[Depends(verify_admin_master_key)])
async def change_subscription_plan(
    company_id: uuid.UUID,
    request: ChangePlanRequest,
    db: AsyncSession = Depends(get_db)
):
    handler = ChangeSubscriptionPlanHandler(db)
    command = ChangeSubscriptionPlanCommand(
        company_id=str(company_id),
        new_plan_id=request.new_plan_id,
        reason=request.reason
    )
    result = await handler.handle(command)
    await db.commit()
    return result


