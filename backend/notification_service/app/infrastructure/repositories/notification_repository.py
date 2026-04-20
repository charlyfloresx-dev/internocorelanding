from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.ports.notification_repository import INotificationRepository
from app.models.preferences import UserPreferences
from app.models.notification import Notification

class SQLAlchemyNotificationRepository(INotificationRepository):
    """
    SQLAlchemy implementation of the Notification Repository.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_preferences(self, user_id: UUID, company_id: UUID) -> Optional[UserPreferences]:
        stmt = select(UserPreferences).where(
            UserPreferences.user_id == user_id,
            UserPreferences.company_id == company_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_notification(self, data: dict) -> Notification:
        notification = Notification(**data)
        self.session.add(notification)
        await self.session.flush()
        # No commit here - application service layer should handle unit of work
        # but since we are refactoring existing code without unit of work, we flush.
        return notification

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        result = await self.session.execute(stmt)
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            await self.session.flush()
            return True
        return False
