from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.domain.entities.viatra_entities import TravelPackage, TravelerGroup, ItineraryItem, PriceAlert

class IPackageRepository(ABC):
    @abstractmethod
    async def get_by_id(self, package_id: UUID, company_id: UUID) -> Optional[TravelPackage]:
        ...

    @abstractmethod
    async def list_all(self, company_id: UUID) -> List[TravelPackage]:
        ...

    @abstractmethod
    async def create(self, package: TravelPackage, user_id: UUID) -> TravelPackage:
        ...

class IGroupRepository(ABC):
    @abstractmethod
    async def get_by_id(self, group_id: UUID, company_id: UUID) -> Optional[TravelerGroup]:
        ...

    @abstractmethod
    async def create(self, group: TravelerGroup, user_id: UUID) -> TravelerGroup:
        ...
    
    @abstractmethod
    async def get_active_groups_with_flights(self) -> List[TravelerGroup]:
        ...

class IItineraryRepository(ABC):
    @abstractmethod
    async def get_active_accommodations(self) -> List[ItineraryItem]:
        ...
    
    @abstractmethod
    async def get_by_id(self, item_id: UUID, company_id: UUID) -> Optional[ItineraryItem]:
        ...

class IPriceAlertRepository(ABC):
    @abstractmethod
    async def create_alert(self, data: dict) -> None:
        ...
