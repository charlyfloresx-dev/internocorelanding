from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from hcm_app.domain.entities.collaborator_entities import Collaborator

class ICollaboratorRepository(ABC):
    @abstractmethod
    async def get_by_internal_id(self, internal_id: str, company_id: UUID) -> Optional[Collaborator]:
        ...

    @abstractmethod
    async def create(self, collaborator: Collaborator) -> Collaborator:
        ...

    @abstractmethod
    async def update(self, collaborator: Collaborator) -> Collaborator:
        ...

    @abstractmethod
    async def list_all(self, company_id: UUID) -> List[Collaborator]:
        ...

    @abstractmethod
    async def get_tenant_config(self, tenant_id: UUID) -> Optional[any]:
        ...
