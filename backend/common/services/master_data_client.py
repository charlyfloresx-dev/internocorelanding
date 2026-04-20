import httpx
import logging
import uuid
from typing import Optional, Dict, Any
from decimal import Decimal
from common.config import settings

logger = logging.getLogger("common.master_data_client")

class MasterDataClient:
    """
    [Phase 63] Standard Client for SSOT Metadata.
    Allows other services to query Warehouse/Location structure and Product properties.
    """
    def __init__(self, base_url: Optional[str] = None):
        # In production/App Runner, this should be the specific service URL
        self.base_url = base_url or settings.MASTER_DATA_SERVICE_URL or "http://master-data-service:8000"

    async def get_location_capacity(self, warehouse_id: uuid.UUID, location_code: str, company_id: uuid.UUID) -> Decimal:
        """
        Queries the SSOT for a specific location's pieces capacity.
        """
        async with httpx.AsyncClient() as client:
            try:
                headers = {"X-Company-ID": str(company_id)}
                # Pointing to the new SSOT endpoint in Master Data
                url = f"{self.base_url}/api/v1/locations/{warehouse_id}/{location_code}/capacity"
                
                response = await client.get(url, headers=headers, timeout=5.0)
                
                if response.status_code == 200:
                    body = response.json()
                    data = body.get("data", {})
                    return Decimal(str(data.get("max_capacity", "0")))
                
                logger.warning(f"Master Data returned {response.status_code} for {location_code} in {warehouse_id}")
                return Decimal("0") # Fallback to unrestricted
                
            except Exception as e:
                logger.error(f"Failed to reach Master Data Service for capacity lookup: {str(e)}")
                return Decimal("0") # Fail-safe: allow operation if SSOT is down (availability over consistency for WMS)

# Global singleton
master_data_client = MasterDataClient()
