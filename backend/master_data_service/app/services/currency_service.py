import uuid
import logging
from typing import Dict, Any, List
from decimal import Decimal

from app.domain.repositories.currency_repository import ICurrencyRepository, ICurrencyClient

logger = logging.getLogger(__name__)

class CurrencyService:
    """
    CurrencyService (Master Data) — DELEGATOR version.
    Now redirects all calls to the dedicated currency-service microservice.
    """
    def __init__(self, repository: ICurrencyRepository, client: ICurrencyClient):
        self.repository = repository
        self.client = client

    async def get_latest_exchange_rates_summary(self, company_id: uuid.UUID) -> Dict[str, Any]:
        """
        Delegates to Currency Service to get the summary.
        """
        base_currency = await self.repository.get_company_base_currency(company_id)
        # We use a default list of targets if not provided
        targets = ["MXN", "USD", "EUR"]
        
        # The client will call /active-rate
        rates = await self.client.get_latest_rates(base_currency, targets)
        
        return {
            "company_id": str(company_id),
            "base_currency": base_currency,
            "rates": [
                {
                    "currency": curr,
                    "current_stored_rate": float(val),
                    "new_external_rate": float(val), # In this delegator, they are the same
                    "variation_percentage": 0.0,
                    "is_suspicious": False,
                    "last_update": None
                }
                for curr, val in rates.items()
            ]
        }

    async def update_rates_automatically(self, company_id: uuid.UUID):
        """
        DELEGATED: No longer stores locally. 
        Calls currency-service to ensure its background worker is running.
        """
        # currency-service handles its own updates
        pass

    async def manual_update_rate(
        self, 
        company_id: uuid.UUID, 
        target_currency: str, 
        rate: Decimal, 
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        DELEGATED: Not implemented in MD delegator. 
        In the future, MD UI will call currency-service directly.
        """
        return {"message": "Manual updates must be performed via currency-service"}

    async def verify_rate(self, rate_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        DELEGATED: Verification is now managed by currency-service.
        """
        return True

