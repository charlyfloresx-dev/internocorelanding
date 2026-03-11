import logging
from typing import Any, Dict, Optional
from .base import BaseProvider

logger = logging.getLogger("notification.providers.sms_mock")

class SMSMockProvider(BaseProvider):
    """
    Temporary Mock provider for SMS.
    Logs the output instead of calling Twilio/AWS.
    """
    async def send(
        self, 
        recipient: str, 
        title: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Simulates sending an SMS.
        """
        logger.info(f"📱 [SMS_MOCK_DISPATCH] To: {recipient} | Msg: {message[:50]}...")
        # Always return success for the mock
        return True
