import httpx
import logging
import uuid
from typing import Dict, Any, Optional
from common.config import settings
from common.context import request_context

logger = logging.getLogger("wms.tickets_client")

class TicketsClient:
    """
    Cliente para la comunicación entre microservicios: WMS -> Tickets Service.
    Se encarga de generar incidencias automáticas (ej: Quiebre de Stock).
    """
    
    # El nombre del host en Docker Compose es tickets-service
    # Usamos el puerto interno 8000 (mapeado a 8004 en el host)
    BASE_URL = "http://tickets-service:8000/api/v1/tickets/"

    @classmethod
    async def create_stock_alert_ticket(
        cls, 
        product_id: uuid.UUID, 
        warehouse_id: uuid.UUID,
        requested_qty: float,
        company_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Crea un ticket de soporte automático por falta de stock.
        """
        ctx = request_context.get()
        
        # Obtener company_id del contexto si no se provee
        if not company_id and ctx:
            company_id = ctx.company_id

        headers = {
            "Content-Type": "application/json",
            "X-Trace-Id": str(ctx.trace_id) if ctx else str(uuid.uuid4()),
            "X-Company-ID": str(company_id) if company_id else "",
            "Authorization": f"Bearer {ctx.token}" if ctx and ctx.token else ""
        }

        payload = {
            "title": f"⚠️ ALERTA STOCK: Producto {product_id}",
            "description": (
                f"Se intentó realizar una venta pero no hay stock suficiente.\n"
                f"Producto ID: {product_id}\n"
                f"Almacén ID: {warehouse_id}\n"
                f"Cantidad Solicitada: {requested_qty}"
            ),
            "priority": "HIGH",
            "type": "INCIDENCIA",
            "tags": ["stock_out", "automatic_alert"]
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                logger.info(f"[*] Generating Stock Alert Ticket for product: {product_id}")
                response = await client.post(cls.BASE_URL, json=payload, headers=headers)
                
                body = response.json()
                if response.status_code in [200, 201]:
                    return body.get("data") if isinstance(body, dict) and "data" in body else body
                
                error_detail = body.get("message") or body.get("detail") or "Unknown error"
                logger.error(f"[!] Tickets Service error ({response.status_code}): {error_detail}")
                return {"status": "error", "detail": error_detail}

            except httpx.RequestError as exc:
                logger.error(f"[!] Connection error to Tickets Service: {exc}")
                return {"status": "error", "detail": "Connection failed"}
            except Exception as e:
                logger.error(f"[!] Unexpected error in TicketsClient: {e}")
                return {"status": "error", "detail": str(e)}

    @classmethod
    async def create_internal_ticket(
        cls, 
        title: str,
        description: str,
        priority: str,
        source_service: str,
        metadata: Dict[str, Any],
        company_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Crea un ticket interno (incidencia técnica) sin requerir auth de usuario.
        """
        headers = {
            "Content-Type": "application/json",
            "X-TRACE-ID": str(uuid.uuid4()),
            "X-COMPANY-ID": str(company_id)
        }

        payload = {
            "title": title,
            "description": description,
            "priority": priority,
            "ticket_type": "Incidencia",
            "source_service": source_service,
            "metadata": metadata
        }

        # La ruta es /api/v1/tickets/internal (asumiendo prefijo del router)
        url = f"{cls.BASE_URL}internal"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                logger.info(f"[*] Dispatching Internal Ticket: {title}")
                response = await client.post(url, json=payload, headers=headers)
                
                body = response.json()
                if response.status_code in [200, 201]:
                    return body.get("data")
                
                logger.error(f"[!] Internal Ticket failed ({response.status_code}): {body}")
                return {"status": "error"}

            except Exception as e:
                logger.error(f"[!] Error in create_internal_ticket: {e}")
                return {"status": "error"}
