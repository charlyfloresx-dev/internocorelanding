import uuid
from abc import ABC, abstractmethod
from typing import Optional, Any

class IProductionEventRepository(ABC):
    @abstractmethod
    def create(self, **kwargs) -> Any:
        pass

    @abstractmethod
    async def get_by_id(self, event_id: uuid.UUID) -> Any:
        pass
    
    @abstractmethod
    async def add(self, event: Any) -> None:
        pass

class IProductionSessionRepository(ABC):
    @abstractmethod
    def create(self, **kwargs) -> Any:
        pass

    @abstractmethod
    async def get_by_resource_id_with_lock(self, resource_id: uuid.UUID) -> Any:
        pass
    
    @abstractmethod
    async def add(self, session: Any) -> None:
        pass
