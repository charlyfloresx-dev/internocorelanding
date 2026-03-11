import uuid
import httpx
from app.domain.interfaces.master_data_client import IMasterDataClient
from common.config import settings

class MasterDataClient(IMasterDataClient):
    """
    Client to interact with Master Data Service (Port 8003).
    Ensures cross-service integrity for Product IDs.
    """
    def __init__(self):
        # In production, this would use service discovery or INT_MASTER_DATA_URL
        self.base_url = "http://master-data-service-api:8000/api/v1"

    async def validate_product(self, product_id: uuid.UUID, company_id: uuid.UUID) -> bool:
        """
        Checks if a product exists and is active in Master Data.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/products/{product_id}",
                    headers={"X-Company-ID": str(company_id)}
                )
                return response.status_code == 200
        except Exception:
            # Fail-closed approach: if service unavailable, assume invalid
            return False
