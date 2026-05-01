import httpx
import logging
from uuid import UUID
from decimal import Decimal
from tickets_app.domain.ports.inventory_client import IInventoryClient
from common.config import settings
from fastapi import HTTPException

logger = logging.getLogger("tickets_inventory_client")

class HttpInventoryClient(IInventoryClient):
    def __init__(self):
        # Fallback for local Docker/Docker-Compose testing
        self.base_url = getattr(settings, "int_inventory_service_url", "http://inventory-service:8000/api/v1")
    
    async def record_consumption(
        self, 
        company_id: UUID, 
        resource_id: UUID, 
        warehouse_id: UUID, 
        quantity: Decimal, 
        reference: str,
        user_id: UUID
    ) -> bool:
        """
        Llama al inventory_service para registrar un movimiento OUT en el Kardex.
        Incluye company_id, warehouse_id para validación de precios y stock.
        Es atómico: si falla, levanta un HTTPException para hacer rollback local.
        """
        url = f"{self.base_url}/transactions/"
        
        payload = {
            "resource_id": str(resource_id),
            "warehouse_id": str(warehouse_id),
            "transaction_type": "OUT",
            "quantity": float(quantity),
            "reference": reference,
            "notes": f"Consumo inter-servicio desde Tickets (Ref: {reference})"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Company-ID": str(company_id),
            "X-User-ID": str(user_id)
        }
        
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code in (200, 201):
                    logger.info(f"Kardex OUT atómico exitoso para resource {resource_id} en warehouse {warehouse_id}")
                    return True
                else:
                    logger.error(f"Error Kardex OUT ({response.status_code}): {response.text}")
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Error en Inventory Service: No se pudo despachar el recurso. Motivo: {response.text}"
                    )
                    
        except httpx.RequestError as e:
            logger.error(f"Network error invocando inventory_service Kardex: {e}")
            raise HTTPException(
                status_code=503, 
                detail="Inventory Service no disponible. El consumo de recursos fue cancelado preventivamente para mantener atomicidad."
            )
