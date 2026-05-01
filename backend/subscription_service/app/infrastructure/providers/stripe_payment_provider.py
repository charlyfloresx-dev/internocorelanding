import stripe
import uuid
from typing import Optional, Dict, Any
from app.core.config import settings
from app.infrastructure.interfaces.payment_provider import IPaymentProvider


class StripePaymentProvider(IPaymentProvider):
    """
    Concrete implementation of IPaymentProvider using Stripe SDK.
    """

    def __init__(self):
        stripe.api_key = settings.stripe.int_stripe_secret_key

    async def create_checkout_session(self, company_id: uuid.UUID, plan_id: str, success_url: str, cancel_url: str) -> str:
        # Note: Stripe SDK is synchronous, so we'd normally run this in a threadpool if performance is a concern
        # or use an async stripe client if available. For now, matching existing logic.
        session = stripe.checkout.Session.create(
            ui_mode="embedded",
            line_items=[
                {
                    "price": plan_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            return_url=success_url,
            client_reference_id=str(company_id),
            metadata={
                "company_id": str(company_id),
                "app": "InternoCore"
            }
        )
        return session.client_secret

    async def get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        sub = stripe.Subscription.retrieve(subscription_id)
        return {
            "id": sub.id,
            "status": sub.status,
            "customer": sub.customer,
            "current_period_end": sub.current_period_end,
            "plan_id": sub.plan.id if sub.plan else None,
        }

    async def cancel_subscription(self, subscription_id: str) -> bool:
        stripe.Subscription.delete(subscription_id)
        return True

    async def verify_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        # Dev bypass for 'stripe trigger' sensorial validation
        if settings.ENV_MODE == "development" and not settings.stripe.int_stripe_webhook_secret:
            import json
            event_data = json.loads(payload)
            return {
                "type": event_data.get("type"),
                "data": event_data.get("data", {}).get("object")
            }

        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe.int_stripe_webhook_secret
        )
        return {
            "type": event.type,
            "data": event.data.object
        }
