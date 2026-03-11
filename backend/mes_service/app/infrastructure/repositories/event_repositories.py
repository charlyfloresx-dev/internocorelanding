import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.repositories.event_interfaces import IProductionEventRepository, IProductionSessionRepository
from app.models.production_event import ProductionEvent
from app.models.production_session import ProductionSession

class SQLAlchemyProductionEventRepository(IProductionEventRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    def create(self, **kwargs) -> Any:
        return ProductionEvent(**kwargs)
    async def get_by_id(self, event_id: uuid.UUID) -> Any:
        return await self.db.get(ProductionEvent, event_id)
    async def add(self, event: Any) -> None:
        self.db.add(event)

class SQLAlchemyProductionSessionRepository(IProductionSessionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    def create(self, **kwargs) -> Any:
        return ProductionSession(**kwargs)
    async def get_by_resource_id_with_lock(self, resource_id: uuid.UUID) -> Any:
        stmt = (
            select(ProductionSession)
            .where(ProductionSession.resource_id == resource_id)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    async def add(self, session: Any) -> None:
        self.db.add(session)
