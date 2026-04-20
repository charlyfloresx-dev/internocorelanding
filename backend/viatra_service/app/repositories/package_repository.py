import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.package import TravelPackage
from app.repositories.base import BaseRepository

class PackageRepository(BaseRepository[TravelPackage]):
    def __init__(self, session: AsyncSession):
        super().__init__(TravelPackage, session)

    async def get_active_packages(self, company_id: uuid.UUID) -> List[TravelPackage]:
        stmt = select(TravelPackage).where(
            TravelPackage.company_id == company_id,
            TravelPackage.is_active == True
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
