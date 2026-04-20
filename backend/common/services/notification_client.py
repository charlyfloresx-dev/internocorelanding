import httpx
import logging
from typing import Dict, Any, Optional
from common.config import settings

logger = logging.getLogger("common.notification_client")

class NotificationClient:
    """
    Cliente liviano para delegar el envío de notificaciones (Email, SMS, Webhooks)
    al microservicio de notificaciones centralizado.
    """
    def __init__(self, base_url: Optional[str] = None):
        # Por defecto intenta conectar al contenedor 'notification-service' en la red de Docker
        self.base_url = base_url or "http://notification-service:8000"

    async def send_event(self, event_type: str, payload: Dict[str, Any], company_id: str) -> bool:
        """
        Envía un evento al notification_service para que este lo procese y despache.
        """
        async with httpx.AsyncClient() as client:
            try:
                # Añadimos metadatos requeridos por el receptor de eventos
                full_payload = {
                    "event_type": event_type,
                    **payload
                }
                
                headers = {"X-Company-ID": company_id}
                
                response = await client.post(
                    f"{self.base_url}/events/",
                    json=full_payload,
                    headers=headers,
                    timeout=5.0
                )
                
                if response.status_code >= 400:
                    logger.error(f"Notification Service devolvió error {response.status_code}: {response.text}")
                    return False
                    
                return True
            except Exception as e:
                logger.error(f"No se pudo contactar con Notification Service: {str(e)}")
                return False

    async def send_user_invitation(self, email: str, code: str, company_name: str, company_id: str) -> bool:
        """
        Helper específico para enviar invitaciones de nuevos usuarios.
        """
        payload = {
            "user_email": email,
            "invitation_code": code,
            "company_name": company_name
        }
        return await self.send_event("UserInvitationEvent", payload, company_id)

# Instancia global para ser inyectada/usada en los endpoints
notification_client = NotificationClient()
