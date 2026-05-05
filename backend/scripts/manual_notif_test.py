import asyncio
import uuid
from common.infrastructure.database import AsyncSessionLocal
from notification_app.services.notification_service import NotificationService
from notification_app.models.notification import NotificationCategory, NotificationPriority

async def manual_notify():
    async with AsyncSessionLocal() as db:
        svc = NotificationService(db)
        company_id = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
        
        print("DEBUG: Sending manual notification to role 'admin'...")
        try:
            notif = await svc.notify_role(
                company_id=company_id,
                role_name="admin",
                title="🔔 TEST MANUAL: Notificación de Prueba",
                message="Esta es una notificación generada manualmente para validar el sistema.",
                category=NotificationCategory.SYSTEM,
                priority=NotificationPriority.HIGH,
                action_url="/dashboard",
                metadata={"test": True}
            )
            await db.commit()
            print(f"DEBUG: Notification created with ID: {notif.id}")
        except Exception as e:
            print(f"DEBUG: Error creating notification: {e}")

if __name__ == "__main__":
    asyncio.run(manual_notify())
