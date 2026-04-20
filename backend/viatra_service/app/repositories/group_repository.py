import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.group import TravelerGroup
from app.repositories.base import BaseRepository

class GroupRepository(BaseRepository[TravelerGroup]):
    def __init__(self, session: AsyncSession):
        super().__init__(TravelerGroup, session)

    async def get_groups_by_package(self, package_id: uuid.UUID, company_id: uuid.UUID) -> List[TravelerGroup]:
        stmt = select(TravelerGroup).where(
            TravelerGroup.package_id == package_id,
            TravelerGroup.company_id == company_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
