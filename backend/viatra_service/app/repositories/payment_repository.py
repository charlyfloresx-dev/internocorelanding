import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment_history import PaymentHistory
from app.repositories.base import BaseRepository

class PaymentRepository(BaseRepository[PaymentHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(PaymentHistory, session)

    async def get_by_stripe_session_id(self, session_id: str, company_id: uuid.UUID) -> Optional[PaymentHistory]:
        query = select(self.model).where(
            self.model.stripe_session_id == session_id,
            self.model.company_id == company_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
