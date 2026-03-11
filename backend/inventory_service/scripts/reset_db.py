import asyncio
import os
import sys
from sqlalchemy import text

# Ajuste de path para encontrar 'app' y 'common'
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICE_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BACKEND_ROOT)
sys.path.insert(0, SERVICE_APP)

from app.db.session import engine

async def reset_db():
    print("🧹 [INVENTORY] Dropping and recreating public schema...")
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO current_user;"))
    print("✅ [INVENTORY] Schema reset successful.")

if __name__ == "__main__":
    asyncio.run(reset_db())
