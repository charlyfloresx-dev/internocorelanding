import httpx
import logging
from decimal import Decimal
from typing import Dict, List, Optional
from master_app.domain.repositories.currency_repository import ICurrencyClient
from common.config import settings

logger = logging.getLogger(__name__)

class ExternalCurrencyClient(ICurrencyClient):
    """
    Real implementation of ICurrencyClient calling the dedicated currency-service.
    """
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.int_currency_service_url
        self.timeout = 5.0

    async def get_latest_rates(self, base_currency: str, targets: List[str]) -> Dict[str, Decimal]:
        """
        Fetches active rates from the Currency microservice.
        """
        url = f"{self.base_url}/api/v1/currencies/active-rate"
        params = {
            "base": base_currency,
            "targets": ",".join(targets)
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                rates_data = data.get("rates", {})
                
                # Convert to Decimal
                return {curr: Decimal(str(val)) for curr, val in rates_data.items()}
                
        except Exception as e:
            logger.error(f"❌ Error fetching rates from Currency Service: {str(e)}")
            # Fallback (optional, or raise)
            return {}

class DummyCurrencyClient(ICurrencyClient):
    """
    Mock implementation for development/testing without real currency-service.
    """
    async def get_latest_rates(self, base_currency: str, targets: List[str]) -> Dict[str, Decimal]:
        # Return 1:1 rates as fallback
        return {curr: Decimal("1.0") for curr in targets}
