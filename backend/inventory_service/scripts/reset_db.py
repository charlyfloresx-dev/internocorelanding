import asyncio
import os
import sys
from sqlalchemy import text

# Path normalization — Docker (WORKDIR=/app) compatible
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

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
