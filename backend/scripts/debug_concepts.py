import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

MASTER_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
COMPANY_ID = "11111111-1111-4111-8111-123456789abc"

async def debug_concepts():
    engine = create_async_engine(MASTER_DB_URL)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id, name, type FROM movement_concepts WHERE company_id = :cid"), {"cid": COMPANY_ID})
        rows = res.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Name: {row[1]}, Type: {row[2]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_concepts())
