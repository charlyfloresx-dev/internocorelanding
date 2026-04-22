import uuid
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa
from auth_app.domain.repositories.user_company_role_repository import IUserCompanyRoleRepository
from auth_app.domain.entities.user_aggregate import UserCompanyRoleEntity
from auth_app.models import UserCompanyRole
from common.models import Company

class SQLAlchemyUserCompanyRoleRepository(IUserCompanyRoleRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_and_company(self, user_id: uuid.UUID, company_id: uuid.UUID) -> Optional[UserCompanyRoleEntity]:
        stmt = (
            select(UserCompanyRole)
            .where(sa.and_(UserCompanyRole.user_id == user_id, UserCompanyRole.company_id == company_id))
            .options(
                selectinload(UserCompanyRole.role),
                selectinload(UserCompanyRole.company)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        if not models:
            return None
            
        role_names = [m.role.name for m in models if m.role]
        
        # Combinar scopes de todos los roles
        all_scopes = set()
        for m in models:
            if m.scopes:
                all_scopes.update(m.scopes)

        # Fetch company directly in case lazy load didn't work
        company_name = None
        group_id = None
        first_model = models[0]
        
        if first_model.company:
            company_name = first_model.company.name
            group_id = first_model.company.parent_group_id
        else:
            # Fallback: explicit DB query
            company_obj = await self.session.get(Company, company_id)
            if company_obj:
                company_name = company_obj.name
                group_id = company_obj.parent_group_id
                
        return UserCompanyRoleEntity(
            company_id=company_id,
            company_name=company_name,
            role_names=role_names,
            scopes=list(all_scopes),
            group_id=group_id
        )
