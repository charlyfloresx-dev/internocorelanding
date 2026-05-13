import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

MASTER_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"

async def check_enums():
    engine = create_async_engine(MASTER_DB_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT DISTINCT type FROM movement_concepts"))
        print(f"Movement Concepts Types: {[row[0] for row in res.fetchall()]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_enums())
