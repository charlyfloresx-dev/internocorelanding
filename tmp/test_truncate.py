import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_truncate():
    engine = create_async_engine('postgresql+asyncpg://user:password@localhost:5433/viatra_db')
    async with engine.begin() as conn:
        print("🧹 Truncating...")
        await conn.execute(text("TRUNCATE viatra_traveler_groups, viatra_travel_packages CASCADE"))
        print("✅ Truncated.")
        res = await conn.execute(text("SELECT count(*) FROM viatra_travel_packages"))
        print(f"Count after truncate: {res.scalar()}")

if __name__ == "__main__":
    asyncio.run(test_truncate())
