import hmac
import hashlib
import json
import httpx
import logging
from typing import Dict, Any, Optional
from common.config import settings

logger = logging.getLogger("notifications.webhook_provider")

class WebhookProvider:
    """
    Provider for dispatching signed external webhooks (Slack, Email relays, etc.).
    Uses HMAC-SHA256 for integrity verification by the receiver.
    Migrated from Tickets Service to enforce Centralized Notification architecture.
    """
    
    # Ideally stored in settings or Secrets Manager
    WEBHOOK_SECRET = getattr(settings, "int_webhook_secret", "dummy_static_secret_for_signing").encode('utf-8')

    @classmethod
    def _sign_payload(cls, payload: Dict[str, Any]) -> str:
        """
        Generates HMAC-SHA256 signature for the given payload.
        """
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        signature = hmac.new(cls.WEBHOOK_SECRET, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature

    @classmethod
    async def dispatch_webhook(cls, event_type: str, ticket_data: Dict[str, Any], target_url: str):
        """
        Dispatches a signed webhook payload to an external provider.
        """
        payload = {
            "event": event_type,
            "data": ticket_data,
            "source": "INTERNO_CORE_NOTIFICATION_SERVICE"
        }
        
        signature = cls._sign_payload(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-Interno-Signature-256": signature
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                # Fire and forget / background dispatch
                response = await client.post(target_url, json=payload, headers=headers)
                if response.status_code >= 400:
                    logger.warning(f"Webhook dispatch to {target_url} failed with status {response.status_code}")
                else:
                    logger.info(f"Successfully dispatched webhook event '{event_type}' to {target_url}")
            except Exception as e:
                logger.error(f"Failed to dispatch webhook to {target_url}: {e}")
