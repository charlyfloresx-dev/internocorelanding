import asyncio
import sys
import os

# Add /app to path
sys.path.append("/app")

from sqlalchemy import text
from app.dependencies.database import engine
# Import all models to ensure they are registered
import app.models.event_log
import app.models.notification
import app.models.preferences

async def init_models():
    async with engine.begin() as conn:
        print("Creating/Updating tables for Notification Service...")
        # Drop only specific tables for schema update
        await conn.execute(text("DROP TABLE IF EXISTS notification_recipients CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS notifications CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS notif_processed_events CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS notification_preferences CASCADE"))
        
        # Create all (won't affect existing tables that aren't in this service's models)
        from common.models import MultiTenantBase
        await conn.run_sync(MultiTenantBase.metadata.create_all)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(init_models())
