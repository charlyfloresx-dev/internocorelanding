
import asyncio
from common.infrastructure.database import AsyncSessionLocal
from sqlalchemy import text

async def fix():
    async with AsyncSessionLocal() as session:
        # 1. Get current status for debugging
        res = await session.execute(text("SELECT id, name, status FROM companies"))
        companies = res.fetchall()
        print("--- Current Status ---")
        for c in companies:
            print(f"ID: {c.id}, Name: {c.name}, Status: {c.status}")
        
        # 2. Set all to ACTIVE
        print("\nUpdating all companies to ACTIVE...")
        await session.execute(text("UPDATE companies SET status = 'ACTIVE'"))
        await session.commit()
        
        # 3. Verify
        res = await session.execute(text("SELECT id, name, status FROM companies"))
        companies = res.fetchall()
        print("\n--- New Status ---")
        for c in companies:
            print(f"ID: {c.id}, Name: {c.name}, Status: {c.status}")

if __name__ == "__main__":
    asyncio.run(fix())
