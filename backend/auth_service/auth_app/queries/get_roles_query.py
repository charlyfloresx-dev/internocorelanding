from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from common.cqrs import IQuery, IQueryHandler
from auth_app.models import Role
from auth_app.schemas.role import RoleResponse

class GetRolesQuery(IQuery[List[RoleResponse]]):
    pass

class GetRolesQueryHandler(IQueryHandler[List[RoleResponse]]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def handle(self, query: GetRolesQuery) -> List[RoleResponse]:
        stmt = select(Role)
        result = await self.db.execute(stmt)
        roles = result.scalars().all()
        return [RoleResponse.from_orm(role) for role in roles]
