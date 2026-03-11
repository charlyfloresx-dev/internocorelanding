import uuid
from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user_aggregate import UserCompanyRoleEntity

class IUserCompanyRoleRepository(ABC):
    @abstractmethod
    async def get_by_user_and_company(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Optional[UserCompanyRoleEntity]:
        """
        Retrieves the association between a user and a company, including roles and scopes.
        """
        pass
