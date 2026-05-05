import logging
import stripe
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from subscription_app.core.config import settings
from common.infrastructure.database import get_db
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository
from subscription_app.infrastructure.repositories.sqlalchemy_subscription_repository import SQLAlchemySubscriptionRepository
from common.responses import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Stripe with the API Key
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY


async def get_subscription_repo(session: AsyncSession = Depends(get_db)) -> ISubscriptionRepository:
    return SQLAlchemySubscriptionRepository(session)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    repo: ISubscriptionRepository = Depends(get_subscription_repo),
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook para recibir eventos de Stripe (Ej. invoice.payment_failed).
    Actualiza el estado de la suscripción local para disparar el Muro de Hierro.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET is not configured.")
        raise HTTPException(status_code=500, detail="Webhook configuration error")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info(f"Received Stripe Webhook: {event['type']}")

    if event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        stripe_subscription_id = invoice.get("subscription")
        
        if stripe_subscription_id:
            logger.warning(f"Payment failed for subscription {stripe_subscription_id}. Transitioning to PAST_DUE.")
            await handle_subscription_status_change(repo, db, stripe_subscription_id, "PAST_DUE", True)
            
    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        stripe_subscription_id = invoice.get("subscription")
        
        if stripe_subscription_id:
            logger.info(f"Payment succeeded for subscription {stripe_subscription_id}. Restoring to ACTIVE.")
            await handle_subscription_status_change(repo, db, stripe_subscription_id, "ACTIVE", False)
            
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        stripe_subscription_id = subscription.get("id")
        
        if stripe_subscription_id:
            logger.warning(f"Subscription canceled {stripe_subscription_id}. Transitioning to CANCELED.")
            await handle_subscription_status_change(repo, db, stripe_subscription_id, "CANCELED", True)

    return {"status": "success"}


async def handle_subscription_status_change(
    repo: ISubscriptionRepository, 
    db: AsyncSession, 
    stripe_subscription_id: str, 
    new_status: str,
    readonly: bool
):
    """Actualiza el estado de la suscripción basada en el ID de suscripción de Stripe."""
    # Note: ISubscriptionRepository must have a way to find by stripe_subscription_id.
    # If not, we will need to add it. For now, we query it using raw SQL or ORM.
    from subscription_app.models.subscription import Subscription
    from sqlalchemy import select

    stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.error(f"Subscription not found for Stripe ID: {stripe_subscription_id}")
        return

    subscription.status = new_status
    subscription.readonly = readonly
    await db.commit()
    logger.info(f"Subscription {subscription.id} (Company: {subscription.company_id}) state updated to {new_status} (Readonly: {readonly}).")
