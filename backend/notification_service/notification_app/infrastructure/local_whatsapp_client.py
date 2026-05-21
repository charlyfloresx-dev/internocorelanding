import logging
from typing import Optional, Dict, Any

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from notification_app.infrastructure.base_whatsapp import BaseWhatsAppClient
from notification_app.infrastructure.whatsapp_client import WhatsAppClientError

logger = logging.getLogger(__name__)


class _LocalGatewaySettings(BaseSettings):
    """Lightweight settings for the local WhatsApp gateway (monolith context)."""
    gateway_url: str = Field(default="http://interno-whatsapp-gateway-dev:3000", validation_alias="CORE_LOCAL_WHATSAPP_GATEWAY_URL")
    api_key: str = Field(default="DEV_INTERNAL_KEY_123", validation_alias="CORE_WHATSAPP_GATEWAY_API_KEY")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True)


_gw_settings = _LocalGatewaySettings()


class LocalWhatsAppClient(BaseWhatsAppClient):
    """
    Client for our local multitenant WhatsApp Web Gateway.
    Sends plain-text messages or locally rendered templates via Express.
    """
    def __init__(self):
        self.gateway_url = _gw_settings.gateway_url.rstrip('/')
        self.api_key = _gw_settings.api_key
        self._client = httpx.AsyncClient(timeout=10.0)

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def close(self):
        await self._client.aclose()

    async def send_group_message(
        self,
        group_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        company_id = metadata.get("company_id") if metadata else None
        if not company_id:
            logger.warning("⚠️ No company_id provided in metadata for Local WhatsApp send.")
            raise WhatsAppClientError(
                message="Missing company_id metadata required for multitenant local gateway isolation.",
                status_code=400
            )

        payload = {
            "company_id": str(company_id),
            "to": group_id,
            "message": message
        }

        try:
            logger.info(f"📤 Local WhatsApp: POSTing message to {group_id} for company {company_id}")
            response = await self._client.post(
                f"{self.gateway_url}/api/v1/whatsapp/send",
                json=payload,
                headers=self._get_headers()
            )

            if response.status_code == 200:
                logger.info(f"✅ Local WhatsApp: Message sent successfully for company {company_id}")
                return response.json()
            else:
                error_body = response.text
                logger.error(f"❌ Local WhatsApp: Gateway returned status {response.status_code}: {error_body}")
                raise WhatsAppClientError(
                    message=f"Local WhatsApp Gateway returned status {response.status_code}",
                    status_code=response.status_code,
                    response_body=error_body
                )
        except httpx.HTTPError as e:
            logger.error(f"❌ Local WhatsApp: Network error connecting to Gateway: {str(e)}")
            raise WhatsAppClientError(
                message=f"Could not connect to local WhatsApp Gateway: {str(e)}"
            )

    async def send_template_message(
        self,
        group_id: str,
        template_name: str,
        template_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        params_str = ", ".join([f"{k}={v}" for k, v in (template_params or {}).items()])
        message_body = f"[{template_name}] {params_str}"

        company_id = (template_params or {}).get("company_id")
        if not company_id:
            logger.warning("⚠️ No company_id provided in template_params for Local WhatsApp template send.")

        metadata = {"company_id": company_id} if company_id else None
        return await self.send_group_message(group_id, message_body, metadata)
