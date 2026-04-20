import resend
import logging
from typing import Any, Dict, Optional
from app.core.config import settings
from .base import BaseEmailProvider

logger = logging.getLogger("notification.providers.resend")

class ResendEmailProvider(BaseEmailProvider):
    """
    Concrete implementation of Email Provider using Resend SDK.
    """
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        if self.api_key:
            resend.api_key = self.api_key
        else:
            logger.warning("RESEND_API_KEY not found in settings. Email delivery will likely fail.")

    async def send(
        self, 
        recipient: str, 
        title: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Sends an email using Resend.
        """
        if not self.api_key:
            logger.error("Attempted to send email but RESEND_API_KEY is missing.")
            return False

        try:
            # Multi-tenancy: attach company_id to metadata if available
            company_id = metadata.get("company_id") if metadata else None
            
            params = {
                "from": "Interno Core <notifications@resend.dev>", # Default sandbox sender
                "to": [recipient],
                "subject": title,
                "html": message,
            }
            
            if company_id:
                params["headers"] = {"X-Company-ID": str(company_id)}

            # resend.Emails.send is synchronous in current SDK versions usually, 
            # but we can wrap it if needed or if they have an async version.
            # Assuming standard SDK for now.
            response = resend.Emails.send(params)
            
            logger.info(f"📧 [RESEND_DISPATCH] Sent to {recipient}. ID: {response.get('id')}")
            return True
            
        except Exception as e:
            # Capture the exception as requested in the Fail-Safe requirement
            logger.error(f"❌ [RESEND_ERROR] Failed to send email to {recipient}: {str(e)}")
            return False
