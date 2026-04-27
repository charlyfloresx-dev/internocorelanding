import asyncio
from sqlalchemy import text
from common.infrastructure.database import AsyncSessionLocal

async def check_db():
    async with AsyncSessionLocal() as session:
        try:
            # Check for inventory_documents table
            res = await session.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_name = 'inventory_documents'"))
            table_exists = res.scalar() > 0
            print(f"DEBUG: Table inventory_documents exists: {table_exists}")
            
            if table_exists:
                res = await session.execute(text("SELECT count(*) FROM inventory_documents"))
                print(f"DEBUG: Total documents: {res.scalar()}")
                
                res = await session.execute(text("SELECT count(*) FROM notifications"))
                print(f"DEBUG: Total notifications: {res.scalar()}")
            
        except Exception as e:
            print(f"DEBUG: Error checking DB: {e}")

if __name__ == "__main__":
    asyncio.run(check_db())
