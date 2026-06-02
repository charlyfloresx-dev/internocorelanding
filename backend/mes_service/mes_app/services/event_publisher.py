import json
from typing import Any, Dict

class EventPublisher:
    """
    Simula la publicación de eventos a un Message Broker (RabbitMQ/SNS).
    """
    
    @classmethod
    async def publish(cls, event_name: str, payload: Dict[str, Any]):
        """
        Publica un mensaje. En el futuro esto enviará a una cola real.
        """
        message = {
            "event": event_name,
            "timestamp": "2026-05-01T...",
            "data": payload
        }
        print(f"[EVENT] Publishing {event_name}: {json.dumps(message)}")
        
        # 🚨 INTEGRACIÓN MES-TICKETS: Disparar resolución en Tickets Service
        if event_name == "MES_DOWNTIME_CLOSED":
            await cls._call_tickets_resolution(payload)
            
        return True

    @classmethod
    async def _call_tickets_resolution(cls, payload: Dict[str, Any]):
        """
        Llamada inter-servicio para auto-cierre de tickets asociados.
        """
        import httpx
        import hmac
        import hashlib
        from common.config import settings
        
        company_id = payload.get("company_id")
        station_id = payload.get("station_id")
        
        if not company_id or not station_id:
            return

        # Generar firma HMAC para seguridad inter-servicio
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            company_id.encode(),
            hashlib.sha256
        ).hexdigest()

        base_url = getattr(settings, "int_tickets_service_url", settings.int_gateway_url)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/api/v1/tickets/internal/resolve-by-station",
                    params={
                        "station_id": station_id,
                        "trigger_event": "MES_DOWNTIME_CLOSED"
                    },
                    headers={
                        "X-Company-ID": company_id,
                        "X-Service-Signature": signature
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    print(f"[INTEGRATION] Tickets resolved: {response.json().get('message')}")
                else:
                    print(f"[INTEGRATION] Error resolving tickets: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[INTEGRATION] Connection failed to Tickets Service: {str(e)}")
