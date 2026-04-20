"""
ItineraryRepository — Acceso SQLAlchemy a ItineraryItem para StayGuardian.
"""
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.itinerary import ItineraryItem
from app.repositories.base import BaseRepository


class ItineraryRepository(BaseRepository[ItineraryItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(ItineraryItem, session)

    async def get_active_accommodations(self, company_id: Optional[uuid.UUID] = None) -> List[ItineraryItem]:
        """Obtiene ItineraryItems de tipo ACCOMMODATION de todos los grupos activos."""
        stmt = select(ItineraryItem).where(
            ItineraryItem.item_type == "ACCOMMODATION",
            ItineraryItem.is_active == True
        )
        if company_id:
             stmt = stmt.where(ItineraryItem.company_id == company_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_group(self, group_id: uuid.UUID, company_id: uuid.UUID) -> List[ItineraryItem]:
        stmt = select(ItineraryItem).where(
            ItineraryItem.group_id == group_id,
            ItineraryItem.company_id == company_id,
            ItineraryItem.is_active == True
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
