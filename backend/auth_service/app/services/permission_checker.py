import uuid
import logging
from typing import Set
from app.domain.repositories.permission_repository import IPermissionRepository

logger = logging.getLogger(__name__)

class PermissionChecker:
    def __init__(self, permission_repo: IPermissionRepository):
        self.repo = permission_repo

    async def get_user_permissions(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Set[str]:
        """
        Recupera todos los slugs de permisos para un usuario en una empresa específica.
        Zero infrastructure leaks.
        """
        return await self.repo.get_user_permissions(user_id, company_id)

    async def has_permission(self, user_id: uuid.UUID, company_id: uuid.UUID, permission_slug: str) -> bool:
        """
        Verifica si un usuario tiene un permiso específico.
        """
        permissions = await self.get_user_permissions(user_id, company_id)
        return permission_slug in permissions
