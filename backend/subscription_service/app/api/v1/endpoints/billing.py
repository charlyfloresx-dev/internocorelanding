import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from typing import Any

from app.services.billing_service import BillingService
from app.services.webhook_service import WebhookService
from app.dependencies.repositories import get_subscription_repository, get_payment_provider
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.infrastructure.interfaces.payment_provider import IPaymentProvider

router = APIRouter()


def get_billing_service(
    repo: ISubscriptionRepository = Depends(get_subscription_repository),
    provider: IPaymentProvider = Depends(get_payment_provider)
) -> BillingService:
    return BillingService(repo, provider)


def get_webhook_service(
    billing: BillingService = Depends(get_billing_service),
    provider: IPaymentProvider = Depends(get_payment_provider),
    repo: ISubscriptionRepository = Depends(get_subscription_repository)
) -> WebhookService:
    return WebhookService(billing, provider, repo)


@router.post("/sessions/create-embedded", status_code=status.HTTP_201_CREATED)
async def create_checkout_session(
    x_company_id: uuid.UUID = Header(...),
    user_email: str = "charly.flores.x@gmail.com",
    service: BillingService = Depends(get_billing_service)
):
    """
    Crea una sesión de Stripe Embedded Checkout para la empresa especificada.
    """
    try:
        client_secret = await service.create_membership_session(x_company_id, user_email)
        return {
            "status": "success",
            "data": {
                "client_secret": client_secret
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Endpoint para recibir notificaciones de eventos de Stripe.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    # Dev bypass for 'stripe trigger' without secret
    from app.core.config import settings
    if not sig_header and settings.ENV_MODE == "development" and not settings.stripe.int_stripe_webhook_secret:
        sig_header = "dev_bypass"
    
    if not sig_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Falta firma")

    result = await service.process_event(payload, sig_header)
    
    if result is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firma inválida o error en proceso")
    
    if result == "ignored":
        return {"status": "ignored"}
        
    return {"status": "success"}
