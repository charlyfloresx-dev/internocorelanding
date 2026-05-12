import asyncio
import uuid
from sqlalchemy import select
from common.infrastructure.database import AsyncSessionLocal
from notification_app.models.notification import Notification, NotificationRecipient

async def check_notifs():
    # User Charly ID (from previous logs/seed)
    CHARLY_ID = uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000001")
    
    async with AsyncSessionLocal() as db:
        query = (
            select(Notification.id, Notification.title, NotificationRecipient.is_read)
            .join(NotificationRecipient, Notification.id == NotificationRecipient.notification_id)
            .where(NotificationRecipient.user_id == CHARLY_ID)
            .order_by(Notification.created_at.desc())
        )
        result = await db.execute(query)
        rows = result.all()
        
        print(f"--- Notifications for Charly ({CHARLY_ID}) ---")
        for rid, title, is_read in rows:
            print(f"ID: {rid} | Read: {is_read} | Title: {title}")

if __name__ == "__main__":
    asyncio.run(check_notifs())
