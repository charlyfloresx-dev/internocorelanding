from typing import Optional, Dict, Any
from .base import BaseProvider
from .email_resend import ResendEmailProvider
from .sms_mock import SMSMockProvider
# Import existing providers if they were there (Push, Webhook)
# For now, let's just make sure EMAIL and SMS are handled correctly as per requirements.

_PROVIDER_CACHE: Dict[str, BaseProvider] = {}

def get_provider(channel: str) -> Optional[BaseProvider]:
    """
    Factory to retrieve or instantiate the appropriate provider for a channel.
    """
    channel_upper = channel.upper()
    
    if channel_upper in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[channel_upper]
    
    provider = None
    if channel_upper == "EMAIL":
        provider = ResendEmailProvider()
    elif channel_upper == "SMS":
        provider = SMSMockProvider()
    # PUSH and WEBHOOK could be added here if needed, 
    # but let's stick to Phase 10.5 requirements first.
    
    if provider:
        _PROVIDER_CACHE[channel_upper] = provider
        
    return provider
