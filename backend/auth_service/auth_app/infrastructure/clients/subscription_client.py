import hmac
import hashlib
import httpx
import logging
from typing import List, Optional
from auth_app.core.config import settings

logger = logging.getLogger(__name__)


def _service_signature(company_id: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        company_id.encode(),
        hashlib.sha256
    ).hexdigest()


class SubscriptionClient:
    def __init__(self):
        self.base_url = settings.SUBSCRIPTION_SERVICE_URL
        self.timeout = httpx.Timeout(5.0, connect=2.0)

    async def get_company_entitlements(self, company_id: str, correlation_id: Optional[str] = None) -> dict:
        """
        Obtiene el objeto completo de suscripción y módulos.
        Retorna fallback seguro si hay error.
        """
        url = f"{self.base_url}/internal/entitlements/{company_id}"
        headers = {"X-Service-Signature": _service_signature(company_id)}
        if correlation_id:
            headers["X-Transaction-ID"] = correlation_id

        fallback = {
            "modules": ["auth_core", "inventory_core"],
            "status": "TRIAL",
            "readonly": True
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return response.json()
                
                logger.warning(f"⚠️ Subscription Service returned {response.status_code} for {company_id}")
                return fallback
                
        except Exception as e:
            logger.error(f"❌ Error connecting to Subscription Service: {e}")
            return fallback
