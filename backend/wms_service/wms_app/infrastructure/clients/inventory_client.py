import uuid
import httpx
from wms_app.domain.interfaces.inventory_client import IInventoryClient
from wms_app.core.config import settings

class InventoryClient(IInventoryClient):
    """
    HTTP Client for communicating with the Inventory Service (Port 8006).
    Replaces direct module imports to enforce microservice boundaries.
    """
    BASE_URL = getattr(settings, "INVENTORY_SERVICE_URL", "http://inventory-service:8006")

    @staticmethod
    async def reserve_stock(
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: float,
        company_id: uuid.UUID,
        token: str
    ) -> dict:
        """Calls POST /inventory/reserve on the Inventory Service."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{InventoryClient.BASE_URL}/api/v1/inventory/reserve",
                json={
                    "warehouse_id": str(warehouse_id),
                    "product_id": str(product_id),
                    "quantity": quantity,
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Company-Id": str(company_id),
                }
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def register_movement(
        warehouse_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: float,
        movement_type: str,
        document_type: str,
        document_id: uuid.UUID,
        company_id: uuid.UUID,
        token: str
    ) -> dict:
        """Calls POST /inventory/movement on the Inventory Service."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{InventoryClient.BASE_URL}/api/v1/inventory/movement",
                json={
                    "warehouse_id": str(warehouse_id),
                    "product_id": str(product_id),
                    "quantity": quantity,
                    "movement_type": movement_type,
                    "document_type": document_type,
                    "document_id": str(document_id),
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Company-Id": str(company_id),
                }
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    async def get_stock(
        company_id: uuid.UUID,
        token: str
    ) -> dict:
        """Calls GET /dashboard/stock on the Inventory Service."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{InventoryClient.BASE_URL}/api/v1/dashboard/stock",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Company-Id": str(company_id),
                }
            )
            response.raise_for_status()
            return response.json()
