from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import UserPreferences

class PreferenceService:
    """Service to determine which notification channels to use for a user.

    - HIGH priority forces all channels (IN_APP, EMAIL, PUSH).
    - For other priorities, respect the UserPreferences flags.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_channels(self, user_id, company_id, priority: str):
        # High priority overrides preferences
        if priority == "HIGH":
            return ["IN_APP", "EMAIL", "PUSH"]

        # Retrieve user preferences for the tenant
        result = await self.db.execute(
            select(UserPreferences).where(
                UserPreferences.user_id == user_id,
                UserPreferences.company_id == company_id,
            )
        )
        pref = result.scalar_one_or_none()
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
