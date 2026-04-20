"""
PriceAlertRepository — Acceso SQLAlchemy a PriceAlert para centinelas.
"""
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.price_alert import PriceAlert
from app.repositories.base import BaseRepository


class PriceAlertRepository(BaseRepository[PriceAlert]):
    def __init__(self, session: AsyncSession):
        super().__init__(PriceAlert, session)

    async def create_alert(self, alert_data: dict) -> PriceAlert:
        """Crea y persiste una alerta de precio/disponibilidad."""
        alert = PriceAlert(**alert_data)
        self.session.add(alert)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
