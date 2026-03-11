import httpx
import logging
import uuid
from typing import Dict, Any, Optional
from common.config import settings
from common.context import request_context

logger = logging.getLogger("inventory.tickets_client")

class TicketsClient:
    """
    Client for Inventory -> Tickets Service communication.
    Responsible for generating Automated Incident Tickets (P1-P4).
    """

    # Tickets Service internally runs on port 8000, mapped to 8004 externally.
    BASE_URL = "http://tickets-service:8000/api/v1/tickets/internal"
    
    SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"

    @classmethod
    async def post_system_alert(
        cls,
        title: str,
        description: str,
        priority: str,
        company_id: uuid.UUID,
        product_id: uuid.UUID,
        warehouse_id: uuid.UUID,
        transaction_id: Optional[uuid.UUID] = None,
        deep_link_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sends an automated alert to the Notification Engine (Tickets Service).
        """
        ctx = request_context.get()
        headers = {
            "Content-Type": "application/json",
            "X-Trace-Id": str(ctx.trace_id) if ctx else str(uuid.uuid4()),
            "X-Company-ID": str(company_id),
            # Bypass JWT, use internal header Identity for SYSTEM_USER
            "x-user-id": cls.SYSTEM_USER_ID
        }

        payload = {
            "title": title,
            "description": description,
            "priority": priority, # P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW mapping
            "ticket_type": "SYSTEM_ALERT",
            "source_service": "INVENTORY_SERVICE",
            "product_id": str(product_id) if product_id else None,
            "warehouse_id": str(warehouse_id) if warehouse_id else None,
            "transaction_id": str(transaction_id) if transaction_id else None,
            "deep_link_id": str(deep_link_id) if deep_link_id else None,
            "metadata": metadata or {}
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.post(cls.BASE_URL, json=payload, headers=headers)
                
                if response.status_code in (200, 201):
                    logger.info(f"[*] Successfully dispatched {priority} Alert to Tickets Service.")
                    body = response.json()
                    return body.get("data")
                
                logger.error(f"[!] Tickets Service rejected alert ({response.status_code}): {response.text}")
                return None

            except httpx.RequestError as exc:
                logger.error(f"[!] Connection error to Tickets Service: {exc}")
                return None
            except Exception as e:
                logger.error(f"[!] Unexpected error in TicketsClient: {e}")
                return None
