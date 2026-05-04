
import asyncio
from common.infrastructure.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT key, label, translation_key FROM movement_concepts"))
        rows = res.fetchall()
        print("--- Movement Concepts ---")
        for r in rows:
            print(f"Key: {r.key}, Label: {r.label}, Translation: {r.translation_key}")

if __name__ == "__main__":
    asyncio.run(check())
