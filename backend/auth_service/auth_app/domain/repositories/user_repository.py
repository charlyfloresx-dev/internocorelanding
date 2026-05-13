from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from uuid import UUID

from auth_app.domain.entities.user_aggregate import UserEntity, UserCompanyRoleEntity

class IUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserEntity]:
        pass

    @abstractmethod
    async def get_user_companies(self, user_id: UUID) -> List[UserCompanyRoleEntity]:
        """Devuelve un listado de las empresas a las que el usuario tiene acceso."""
        pass

    @abstractmethod
    async def get_user_context_for_company(
        self, user_id: UUID, company_id: UUID
    ) -> Tuple[List[str], List[str], Optional[UUID]]:
        """
        Devuelve (roles, scopes, group_id) para un usuario en una empresa.
        """
        pass

    @abstractmethod
    async def update_user_password(self, user_id: UUID, hashed_password: str) -> bool:
        """Actualiza la contraseña de un usuario."""
        pass

    @abstractmethod
    async def register_tenant(self, company_name: str, admin_email: str, admin_password_hash: str, admin_first_name: str, admin_last_name: str) -> UserEntity:
        """Registra un nuevo tenant y administrador."""
        pass

    @abstractmethod
    async def update_user(self, user_id: UUID, update_data: dict, current_user_id: UUID, current_company_id: UUID) -> UserEntity:
        """Actualiza la información de un usuario."""
        pass
