"""
WhatsApp Client Factory — Multitenant Dynamic Resolution
─────────────────────────────────────────────────────────
Resolves the correct WhatsApp client adapter (Twilio or Local Gateway)
for each tenant based on their persisted configuration in
`company_notification_configs`.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.company_notification_model import CompanyNotificationConfig
from app.infrastructure.base_whatsapp import BaseWhatsAppClient
from app.infrastructure.local_whatsapp_client import LocalWhatsAppClient
from app.infrastructure.twilio_whatsapp_client import TwilioWhatsAppClient

logger = logging.getLogger(__name__)


class WhatsAppClientFactory:
    """
    Resolves dynamically the WhatsApp provider for a given tenant:
      1. Queries `company_notification_configs` for the tenant's preference.
      2. Falls back to the global default (from .env) if no config is found.
      3. Supports BYOK (Bring Your Own Key) for Twilio credentials.
    """

    @staticmethod
    async def get_client_for_tenant(db_session: AsyncSession, company_id: str) -> BaseWhatsAppClient:
        query = select(CompanyNotificationConfig).where(
            CompanyNotificationConfig.company_id == company_id,
            CompanyNotificationConfig.is_active == True  # noqa: E712
        )
        result = await db_session.execute(query)
        tenant_config = result.scalar_one_or_none()

        provider = None
        if tenant_config:
            provider = tenant_config.provider  # "twilio" or "local"

        # Fallback to global default if the tenant has no explicit configuration
        if not provider:
            provider = getattr(settings, 'DEFAULT_WHATSAPP_PROVIDER', 'twilio')

        logger.info(f"🔌 Resolving WhatsApp client for Company: {company_id}. Provider: {provider}")

        if provider == "local":
            return LocalWhatsAppClient()

        # Twilio path: use tenant BYOK credentials or fall back to core credentials
        if tenant_config and tenant_config.account_sid and tenant_config.auth_token:
            return TwilioWhatsAppClient(
                account_sid=tenant_config.account_sid,
                auth_token=tenant_config.auth_token,
                sender_number=tenant_config.sender_number,
                base_url=settings.WHATSAPP_BASE_URL
            )

        # Fallback to global Twilio credentials
        return TwilioWhatsAppClient(
            account_sid=settings.TWILIO_ACCOUNT_SID or "",
            auth_token=settings.TWILIO_AUTH_TOKEN or "",
            sender_number=settings.WHATSAPP_SENDER_NUMBER,
            base_url=settings.WHATSAPP_BASE_URL
        )
