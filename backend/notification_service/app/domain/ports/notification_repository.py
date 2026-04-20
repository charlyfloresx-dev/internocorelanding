from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
import uuid

class INotificationRepository(ABC):
    """
    Interface for persistence of notifications and preferences.
    """

    @abstractmethod
    async def get_user_preferences(self, user_id: UUID, company_id: UUID) -> Optional["UserPreferences"]:  # noqa: F821
        """Retrieves user notification settings."""
        ...

    @abstractmethod
    async def save_notification(self, data: dict) -> "Notification":  # noqa: F821
        """Persists a new notification."""
        ...

    @abstractmethod
    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Updates notification read status."""
        ...
