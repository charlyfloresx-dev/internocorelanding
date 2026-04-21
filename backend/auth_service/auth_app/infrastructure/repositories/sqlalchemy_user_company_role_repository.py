import uuid
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from auth_app.domain.repositories.user_company_role_repository import IUserCompanyRoleRepository
from auth_app.domain.entities.user_aggregate import UserCompanyRoleEntity
from auth_app.models import UserCompanyRole

class SQLAlchemyUserCompanyRoleRepository(IUserCompanyRoleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_and_company(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Optional[UserCompanyRoleEntity]:
        stmt = (
            select(UserCompanyRole)
            .where(sa.and_(UserCompanyRole.user_id == user_id, UserCompanyRole.company_id == company_id))
            .options(selectinload(UserCompanyRole.role))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
            
        return UserCompanyRoleEntity(
            company_id=model.company_id,
            role_names=[model.role.name],
            scopes=model.scopes or []
        )
