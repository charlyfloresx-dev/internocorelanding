import uuid
from abc import ABC, abstractmethod
from typing import Set

class IPermissionRepository(ABC):
    @abstractmethod
    async def get_user_permissions(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Set[str]:
        """
        Retrieves all permission slugs for a user in a specific company.
        """
        pass
