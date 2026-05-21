from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseWhatsAppClient(ABC):
    @abstractmethod
    async def send_group_message(
        self,
        group_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a plain-text message to a WhatsApp group/number."""
        pass

    @abstractmethod
    async def send_template_message(
        self,
        group_id: str,
        template_name: str,
        template_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send a template message to a WhatsApp group/number."""
        pass
