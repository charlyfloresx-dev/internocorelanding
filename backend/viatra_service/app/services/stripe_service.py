import stripe
import uuid
from typing import Optional
from app.core.config import get_settings
from app.domain.entities.viatra_entities import TravelPackage

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    @staticmethod
    async def sync_package_to_stripe(package: TravelPackage) -> str:
        """
        Creates a Product and a Price in Stripe for a given TravelPackage.
        Returns the Stripe Price ID.
        """
        # 1. Create Product
        stripe_product = stripe.Product.create(
            name=package.name,
            description=package.description or f"Viaje a {package.destination}",
            metadata={
                "package_id": str(package.id),
                "company_id": str(package.company_id)
            }
        )

        # 2. Create Price (Recurring for subscription)
        # Price is in cents, so we multiply by 100
        # Handling both Decimal and potentially Price/Money object if it leaks
        amount = package.total_price
        if hasattr(amount, 'amount'):
            amount = amount.amount
            
        currency = "usd"
        if hasattr(package.total_price, 'currency'):
            currency = package.total_price.currency.lower()

        amount_in_cents = int(float(amount) * 100)
        
        stripe_price = stripe.Price.create(
            product=stripe_product.id,
            unit_amount=amount_in_cents,
            currency=currency,
            recurring={"interval": "month"}, # Standard for travel installments
            metadata={
                "package_id": str(package.id)
            }
        )

        return stripe_price.id

    @staticmethod
    async def create_checkout_session(
        price_id: str, 
        success_url: str, 
        cancel_url: str,
        customer_email: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Generates a Stripe Checkout Session URL for a subscription.
        """
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email,
            metadata=metadata or {}
        )
        return session.url

    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> stripe.Event:
        """
        Verifies the authenticity of a Stripe Webhook call using the secret.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise Exception("Invalid signature")

