import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.repositories import get_subscription_repository
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.services.queries import GetEntitlementsQuery

router = APIRouter()


@router.get("/status/{company_id}")
async def get_subscription_status(
    company_id: uuid.UUID,
    repo: ISubscriptionRepository = Depends(get_subscription_repository)
):
    """
    Endpoint interno para el Auth Service.
    """
    sub = await repo.get_subscription_by_company(company_id)
    
    if not sub:
        return {
            "status": "EXPIRED",
            "readonly": True,
            "message": "No subscription found for this company"
        }
        
    return {
        "status": sub.status,
        "readonly": sub.readonly,
        "plan_id": str(sub.plan_id)
    }


@router.get("/entitlements/{company_id}")
async def get_company_entitlements(
    company_id: uuid.UUID,
    repo: ISubscriptionRepository = Depends(get_subscription_repository)
):
    query = GetEntitlementsQuery(repo)
    modules_data = await query.execute(company_id)
    return {
        "company_id": str(company_id),
        "modules": modules_data.get("modules", [])
    }
