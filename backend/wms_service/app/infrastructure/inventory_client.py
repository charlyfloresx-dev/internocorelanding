import httpx
import logging
import uuid
from typing import Dict, Any, Optional
from common.config import settings
from common.context import request_context

logger = logging.getLogger("wms.inventory_client")

class InventoryClient:
    """
    Cliente para la comunicaci\u00f3n entre microservicios: WMS -> Inventory Service.
    Se encarga de registrar los asientos contables de inventario (Kardex).
    """
    
    # El nombre del host en Docker Compose es inventory-service
    # Inventory Service runs on port 8000 internally (mapped to 8006 outside)
    BASE_URL = "http://inventory-service:8000/api/v1/inventory"

    @classmethod
    async def _post(cls, endpoint_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía una petición POST al Inventory Service.
        """
        ctx = request_context.get()
        headers = {
            "Content-Type": "application/json",
            "X-Trace-Id": str(ctx.trace_id) if ctx else str(uuid.uuid4()),
            "X-Company-ID": str(ctx.company_id) if ctx else payload.get("company_id", ""),
            "Authorization": f"Bearer {ctx.token}" if ctx and ctx.token else ""
        }

        url = f"{cls.BASE_URL}{endpoint_path}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                logger.info(f"[*] Calling Inventory Service API: {endpoint_path} for product {payload.get('product_id')}")
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code in (200, 201):
                    body = response.json()
                    return body.get("data") if isinstance(body, dict) and "data" in body else body
                
                # Manejo de errores de negocio
                body = response.json()
                error_detail = body.get("message") or body.get("detail") or "Unknown error"
                logger.error(f"[!] Inventory Service error ({response.status_code}): {error_detail}")
                raise Exception(f"Inventory Service Error: {error_detail}")

            except httpx.RequestError as exc:
                logger.error(f"[!] Connection error to Inventory Service: {exc}")
                raise Exception(f"Could not connect to Inventory Service at {url}")
            except Exception as e:
                logger.error(f"[!] Unexpected error in InventoryClient: {e}")
                raise e

    @classmethod
    async def decrease_stock(
        cls, 
        product_id: uuid.UUID, 
        warehouse_id: uuid.UUID, 
        quantity: float, 
        uom_id: uuid.UUID, 
        reference_id: Optional[uuid.UUID] = None, 
        comments: Optional[str] = None,
        fulfill_reservation: bool = False
    ) -> Dict[str, Any]:
        """
        Registra una salida de inventario (egreso) apuntando a /movements
        utilizando transaction_id / document_id para Trazabilidad Cruzada.
        """
        # Note: We send negative quantity to decrement the ledger
        payload = {
            "warehouse_id": str(warehouse_id),
            "product_id": str(product_id),
            "quantity": -float(quantity),
            "movement_type": "OUT",
            "document_type": "SALES_ORDER" if fulfill_reservation else "OUTBOUND",
            "document_id": str(reference_id) if reference_id else str(uuid.uuid4())
        }
        return await cls._post("/movements", payload)

    @classmethod
    async def reserve_stock(
        cls,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        quantity: float,
        uom_id: uuid.UUID,
        reference_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Solicita una reserva atómica de stock en /reserve (Soft-Lock).
        """
        payload = {
            "warehouse_id": str(warehouse_id),
            "product_id": str(product_id),
            "quantity": float(quantity)
        }
        return await cls._post("/reserve", payload)

    @classmethod
    async def release_reservation(
        cls,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        quantity: float,
        uom_id: uuid.UUID,
        reference_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Libera una reserva previa. Puede ser llamado por el Garbage Collector o cancelaciones.
        """
        payload = {
            "warehouse_id": str(warehouse_id),
            "product_id": str(product_id),
            "quantity": float(quantity)
        }
        return await cls._post("/release", payload)

    @classmethod
    async def get_stock_levels(cls, product_id: uuid.UUID, warehouse_id: uuid.UUID, company_id: Optional[uuid.UUID] = None) -> Optional[Dict[str, Any]]:
        """
        Consulta los niveles de stock (Actual y Reservado) para un producto.
        """
        ctx = request_context.get()
        effective_company_id = company_id or (ctx.company_id if ctx else None)
        
        headers = {
            "X-Company-ID": str(effective_company_id) if effective_company_id else "",
            "Authorization": f"Bearer {ctx.token}" if ctx and ctx.token else ""
        }
        
        # El endpoint de consulta suele ser GET /internal/api/v1/inventory/levels
        url = f"http://inventory-service:8000/internal/api/v1/inventory/levels/{product_id}/{warehouse_id}"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    body = response.json()
                    # Extraer 'data' del wrapper global
                    return body.get("data") if isinstance(body, dict) and "data" in body else body
                return None
            except Exception as e:
                logger.error(f"Error fetching stock levels: {e}")
                return None
