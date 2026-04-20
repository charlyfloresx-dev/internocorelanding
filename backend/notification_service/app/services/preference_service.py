from uuid import UUID
from app.domain.ports.notification_repository import INotificationRepository

class PreferenceService:
    """Service to determine which notification channels to use for a user.

    - HIGH priority forces all channels (IN_APP, EMAIL, PUSH).
    - For other priorities, respect the UserPreferences flags.
    """

    def __init__(self, repo: INotificationRepository):
        self.repo = repo

    async def get_user_channels(self, user_id: UUID, company_id: UUID, priority: str):
        # High priority overrides preferences
        if priority == "HIGH":
            return ["IN_APP", "EMAIL", "PUSH"]

        # Retrieve user preferences for the tenant via repository
        pref = await self.repo.get_user_preferences(user_id, company_id)
        
        channels = []
        if pref:
            if pref.receive_in_app:
                channels.append("IN_APP")
            if pref.receive_email:
                channels.append("EMAIL")
            if pref.receive_push:
                channels.append("PUSH")
        else:
            # Default fallback
            channels.append("IN_APP")
        return channels
