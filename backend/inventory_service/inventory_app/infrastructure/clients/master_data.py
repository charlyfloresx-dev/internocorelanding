import uuid
import httpx
import logging
from decimal import Decimal
from datetime import datetime
from typing import Optional
from inventory_app.domain.interfaces.master_data_client import IMasterDataClient

from common.context import request_context
from common.config import settings

logger = logging.getLogger(__name__)

class MasterDataClient(IMasterDataClient):
    """
    Client to interact with Master Data Service (Port 8003).
    Ensures cross-service integrity for Product IDs and UOM Factors.
    """
    def __init__(self):
        self.base_url = f"{settings.int_master_data_service_url}/api/v1"
        self.timeout = httpx.Timeout(5.0, connect=2.0)

    def _get_headers(self, company_id: uuid.UUID, trace_id: Optional[str] = None) -> dict:
        headers = {
            "X-Company-ID": str(company_id),
            "X-Trace-ID": trace_id or str(uuid.uuid4())
        }
        # Inyectar token de la sesión actual si existe en el contexto (Propagación)
        try:
            ctx = request_context.get()
            if ctx and ctx.token:
                headers["Authorization"] = f"Bearer {ctx.token}"
            # God Mode propagation if active in context
            if hasattr(ctx, 'role') and ctx.role == 'GOD_MODE_ADMIN':
                headers["X-Admin-Master-Key"] = "GOD_MODE_ACTIVE"
        except:
            pass
        return headers

    async def get_uom_factor(self, uom_id: uuid.UUID, company_id: uuid.UUID) -> Decimal:
        """
        Retrieves the conversion factor for a specific UOM from Master Data.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/uoms/{uom_id}",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    data = response.json()
                    uom_data = data.get("data", {})
                    factor = uom_data.get("conversion_factor")
                    return Decimal(str(factor)) if factor is not None else Decimal("1.0")
                return Decimal("1.0")
        except Exception as e:
            logger.error(f"Error fetching UOM factor {uom_id}: {str(e)}")
            return Decimal("1.0")

    async def get_location_capacity(self, warehouse_id: uuid.UUID, location_code: str, company_id: uuid.UUID) -> Decimal:
        """
        [Phase 63] Fetches capacity from Master Data structural Source of Truth.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/locations/{warehouse_id}/{location_code}/capacity",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    payload = response.json()
                    data = payload.get("data", {})
                    return Decimal(str(data.get("max_capacity", 0)))
                return Decimal("0")
        except Exception as e:
            logger.error(f"Density Guard Fail-Open: Could not fetch capacity for {location_code}: {str(e)}")
            return Decimal("0") # Fail-open: allow movement if MD is down

    async def get_product_internal_metadata(self, product_id: uuid.UUID, company_id: uuid.UUID, trace_id: Optional[str] = None) -> dict:
        """
        Retrieves product name, SKU and UOM metadata from master_data_service internal endpoint.
        Uses _get_headers() so the Bearer token from request_context is propagated.
        """
        headers = self._get_headers(company_id, trace_id)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/products/internal/{product_id}",
                    headers=headers,
                )

                if response.status_code == 200:
                    payload = response.json()
                    data = payload.get("data", {})
                    return {
                        "name": data.get("name") or data.get("description") or f"Producto {str(product_id)[:8]}",
                        "sku": data.get("sku") or data.get("code"),
                        "uom_name": (data.get("uom") or {}).get("name"),
                    }

                logger.warning(f"MasterData returned {response.status_code} for product {product_id}")

        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.error(f"MasterDataClient timeout/network error for product {product_id}: {e}")
        except Exception as e:
            logger.error(f"MasterDataClient unexpected error for product {product_id}: {e}")

        return {"name": f"Producto {str(product_id)[:8]}", "sku": None, "uom_name": None}

    async def validate_product(self, product_id: uuid.UUID, company_id: uuid.UUID) -> bool:
        """
        Checks if a product exists and is active in Master Data.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/products/{product_id}",
                    headers=self._get_headers(company_id)
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_warehouse(self, warehouse_id: uuid.UUID, company_id: uuid.UUID) -> dict:
        """
        Retrieves warehouse details from Master Data.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/warehouses/{warehouse_id}",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    return response.json().get("data", {})
                return {}
        except Exception as e:
            logger.error(f"Error fetching warehouse {warehouse_id}: {str(e)}")
            return {}

    async def get_partner(self, partner_id: uuid.UUID, company_id: uuid.UUID) -> dict:
        """
        Retrieves business partner details from Master Data.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/partners/{partner_id}",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    return response.json().get("data", {})
                return {}
        except Exception as e:
            logger.error(f"Error fetching partner {partner_id}: {str(e)}")
            return {}

    async def list_warehouses(self, company_id: uuid.UUID) -> list[dict]:
        """
        Lists all warehouses for a company from Master Data.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/warehouses/",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    return response.json().get("data", [])
                return []
        except Exception as e:
            logger.error(f"Error listing warehouses: {str(e)}")
            return []

    async def check_uom_readiness(self, company_id: uuid.UUID) -> bool:
        """
        Checks if the company has basic UOMs configured.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/uoms/",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    return len(data) > 0
                return False
        except Exception as e:
            logger.error(f"Error checking UOM readiness: {str(e)}")
            return False

    async def check_product_readiness(self, company_id: uuid.UUID) -> bool:
        """
        Checks if the company has products registered.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/products/",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    return len(data) > 0
                return False
        except Exception as e:
            logger.error(f"Error checking product readiness: {str(e)}")
            return False

    async def get_product_price_at_date(
        self,
        product_id: uuid.UUID,
        company_id: uuid.UUID,
        as_of: datetime,
        list_index: int = 1,
    ) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/prices/products/{product_id}/price-at",
                    params={"as_of": as_of.isoformat(), "list_index": list_index},
                    headers=self._get_headers(company_id),
                )
                if response.status_code == 200:
                    payload = response.json()
                    data = payload.get("data")
                    if data:
                        return {"amount": Decimal(str(data["amount"])), "currency": data["currency"]}
                return None
        except Exception as e:
            logger.error(f"Error fetching point-in-time price for {product_id}: {str(e)}")
            return None

    async def check_pricing_readiness(self, company_id: uuid.UUID) -> bool:
        """
        Checks if the company has at least some prices configured.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/prices/",
                    headers=self._get_headers(company_id)
                )
                if response.status_code == 200:
                    data = response.json().get("data", [])
                    return len(data) > 0
                return False
        except Exception as e:
            logger.error(f"Error checking pricing readiness: {str(e)}")
            return False
