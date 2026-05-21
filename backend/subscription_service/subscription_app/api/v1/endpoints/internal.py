import uuid
import hmac
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Header
from subscription_app.dependencies.repositories import get_subscription_repository
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository
from subscription_app.services.queries import GetEntitlementsQuery
from subscription_app.core.config import settings

router = APIRouter()


def _verify_service_signature(company_id: str, signature: str | None) -> None:
    if not signature:
        raise HTTPException(status_code=403, detail="Firma de servicio requerida")
    expected = hmac.new(
        settings.SECRET_KEY.encode(),
        company_id.encode(),
        hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=403, detail="Firma de servicio inválida")


@router.get("/status/{company_id}")
async def get_subscription_status(
    company_id: uuid.UUID,
    x_service_signature: str = Header(None, alias="X-Service-Signature"),
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
):
    """Endpoint interno para el Auth Service — requiere HMAC X-Service-Signature."""
    _verify_service_signature(str(company_id), x_service_signature)

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
    x_service_signature: str = Header(None, alias="X-Service-Signature"),
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
):
    """Endpoint interno para Auth/HCM — requiere HMAC X-Service-Signature."""
    _verify_service_signature(str(company_id), x_service_signature)

    query = GetEntitlementsQuery(repo)
    modules_data = await query.execute(company_id)
    return {
        "company_id": str(company_id),
        "modules": modules_data.get("modules", []),
        "status": modules_data.get("status", "ACTIVE"),
        "readonly": modules_data.get("readonly", False)
    }
