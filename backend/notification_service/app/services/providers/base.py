from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseProvider(ABC):
    """
    Abstract base interface for all notification channels (Email, SMS, Push, Webhook).
    """
    @abstractmethod
    async def send(
        self, 
        recipient: str, 
        title: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Generic send method for any provider.
        Returns True on success, False on failure.
        """
        pass

class BaseEmailProvider(BaseProvider, ABC):
    """
    Abstract interface specifically for Email providers.
    Could include logic for templates, attachments, etc. in the future.
    """
    @abstractmethod
    async def send(
        self, 
        recipient: str, 
        title: str, 
        message: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        pass
