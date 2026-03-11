import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class IPaymentProvider(ABC):
    """
    Abstract interface to decouple the service from specific payment gateways (like Stripe).
    """

    @abstractmethod
    async def create_checkout_session(self, company_id: uuid.UUID, plan_id: str, success_url: str, cancel_url: str) -> str:
        """Returns the checkout session URL."""
        ...

    @abstractmethod
    async def get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """Returns normalized subscription data."""
        ...

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool:
        ...

    @abstractmethod
    async def verify_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Verifies the webhook signature and returns the event data."""
        ...
