import uuid
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.domain.repositories.event_interfaces import IProductionEventRepository, IProductionSessionRepository
from mes_app.models.production_event import ProductionEvent
from mes_app.models.production_session import ProductionSession

class SQLAlchemyProductionEventRepository(IProductionEventRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    def create(self, **kwargs) -> Any:
        return ProductionEvent(**kwargs)
    async def get_by_id(self, event_id: uuid.UUID, company_id: Optional[uuid.UUID] = None) -> Any:
        # PENDING: Inject exact tenant query instead of session.get globally
        # if company_id is provided, though get() works strictly with primary keys
        return await self.db.get(ProductionEvent, event_id)
    async def add(self, event: Any) -> None:
        self.db.add(event)

class SQLAlchemyProductionSessionRepository(IProductionSessionRepository):
    def __init__(self, db: AsyncSession):
        self.db = db
    def create(self, **kwargs) -> Any:
        return ProductionSession(**kwargs)
    async def get_by_resource_id_with_lock(self, resource_id: uuid.UUID, company_id: Optional[uuid.UUID] = None) -> Any:
        stmt = select(ProductionSession).where(ProductionSession.resource_id == resource_id)
        if company_id:
             stmt = stmt.where(ProductionSession.company_id == company_id)
        stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalars().first()
    async def add(self, session: Any) -> None:
        self.db.add(session)
