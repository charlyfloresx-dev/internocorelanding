import uuid
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.item import ItemEntity

class IItemRepository(ABC):
    """
    Interface for Item persistence in WMS.
    """
    @abstractmethod
    async def get_by_sku(self, company_id: uuid.UUID, sku: str, version_number: int) -> Optional[ItemEntity]:
        pass

    @abstractmethod
    async def save(self, item: ItemEntity) -> None:
        pass
