import uuid
import sqlalchemy as sa
from typing import Set
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth_app.domain.repositories.permission_repository import IPermissionRepository
from auth_app.models import UserCompanyRole, Role, RolePermission, Permission

class SQLAlchemyPermissionRepository(IPermissionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_permissions(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Set[str]:
        stmt = (
            select(Permission.slug)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserCompanyRole, UserCompanyRole.role_id == Role.id)
            .where(
                sa.and_(
                    UserCompanyRole.user_id == user_id,
                    UserCompanyRole.company_id == company_id
                )
            )
        )
        result = await self.session.execute(stmt)
        return {p for p in result.scalars().all()}
