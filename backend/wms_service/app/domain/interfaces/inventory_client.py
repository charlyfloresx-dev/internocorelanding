import uuid
from abc import ABC, abstractmethod
from typing import List, Dict

class IInventoryClient(ABC):
    """
    Interface for communicating with the Inventory Service.
    """
    @abstractmethod
    async def get_stock(self, company_id: uuid.UUID, token: str) -> List[Dict]:
        """
        Retrieves consolidated stock from Inventory Service.
        """
        pass
