"""
WhatsApp Business API Client (Twilio Implementation)
────────────────────────────────────────────────────
Specific client for Twilio's WhatsApp API.

Features:
  - Basic Authentication (AccountSid + AuthToken).
  - Form-encoded payloads (application/x-www-form-urlencoded).
  - Automatic 'whatsapp:' prefix handling for recipients.
  - Tenacity retries and strict timeouts.
"""
import logging
from typing import Optional, Dict, Any

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)

# ─── RETRY CONFIG ───────────────────────────────────────────────────────────
MAX_RETRIES = 3
BACKOFF_MIN_SECONDS = 1
BACKOFF_MAX_SECONDS = 10
TIMEOUT_SECONDS = 15


class WhatsAppClientError(Exception):
    """Base exception for WhatsApp client failures."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class WhatsAppClient:
    """
    Twilio-specific WhatsApp client.
    """

    def __init__(self, account_sid: str, auth_token: str, sender_number: str, base_url: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.sender = sender_number
        # Base URL for Twilio Messages endpoint: https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json
        self.full_url = f"{base_url.rstrip('/')}/{account_sid}/Messages.json"
        
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(TIMEOUT_SECONDS),
        )

    async def close(self):
        """Gracefully close the underlying HTTP client."""
        await self._client.aclose()

    def _format_recipient(self, recipient_id: str) -> str:
        """Ensures the recipient has the 'whatsapp:' prefix required by Twilio."""
        if recipient_id.startswith("whatsapp:"):
            return recipient_id
        return f"whatsapp:{recipient_id}"

    # ─── CORE: SEND GROUP MESSAGE ───────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=BACKOFF_MIN_SECONDS, max=BACKOFF_MAX_SECONDS),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def send_group_message(
        self,
        group_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a plain-text message to a WhatsApp group via Twilio.
        """
        to_address = self._format_recipient(group_id)
        
        # Twilio uses form-data (x-www-form-urlencoded)
        data = {
            "From": self.sender,
            "To": to_address,
            "Body": message
        }

        logger.info(f"📤 Twilio WhatsApp: Sending message to {to_address}")

        response = await self._client.post(
            self.full_url,
            auth=(self.account_sid, self.auth_token),
            data=data
        )

        if response.status_code >= 400:
            error_body = response.text
            logger.error(
                f"❌ Twilio API Error: {response.status_code} | To: {to_address} | Body: {error_body}"
            )
            raise WhatsAppClientError(
                message=f"Twilio API returned {response.status_code}",
                status_code=response.status_code,
                response_body=error_body,
            )

        result = response.json()
        logger.info(f"✅ Twilio WhatsApp: Message sent successfully (SID: {result.get('sid')})")
        return result

    # ─── TEMPLATE MESSAGES ──────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=BACKOFF_MIN_SECONDS, max=BACKOFF_MAX_SECONDS),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def send_template_message(
        self,
        group_id: str,
        template_name: str,
        template_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Twilio requires a ContentSid for templates in production.
        """
        to_address = self._format_recipient(group_id)
        
        # Note: In Twilio, templates often use 'ContentSid' and 'ContentVariables'
        # if using the new Content API. This is a simplified version.
        data = {
            "From": self.sender,
            "To": to_address,
            "Body": f"Template: {template_name}" # Fallback
        }
        
        if template_params:
            # Simple parameter substitution if not using Content API
            pass

        logger.info(f"📤 Twilio WhatsApp: Sending template {template_name} to {to_address}")

        response = await self._client.post(
            self.full_url,
            auth=(self.account_sid, self.auth_token),
            data=data
        )

        if response.status_code >= 400:
            error_body = response.text
            raise WhatsAppClientError(
                message=f"Twilio API returned {response.status_code} for template",
                status_code=response.status_code,
                response_body=error_body,
            )

        return response.json()
