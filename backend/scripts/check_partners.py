
import asyncio
from common.infrastructure.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        # Check if table exists
        try:
            res = await session.execute(text("SELECT id, name, type, company_id FROM partners"))
            rows = res.fetchall()
            print("--- Partners ---")
            for r in rows:
                print(f"ID: {r.id}, Name: {r.name}, Type: {r.type}, Company: {r.company_id}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
