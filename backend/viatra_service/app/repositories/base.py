import uuid
from typing import TypeVar, Type, Optional, List, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from common.models import MultiTenantBase

T = TypeVar("T", bound=MultiTenantBase)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: uuid.UUID, company_id: uuid.UUID) -> Optional[T]:
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.company_id == company_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, company_id: uuid.UUID) -> List[T]:
        stmt = select(self.model).where(self.model.company_id == company_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, id: uuid.UUID, company_id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(
            self.model.id == id,
            self.model.company_id == company_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
