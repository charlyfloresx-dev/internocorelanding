import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

AUTH_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/dbname"

async def get_users():
    engine = create_async_engine(AUTH_DB_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT id, email FROM users"))
        for row in res.fetchall():
            print(f"ID: {row[0]}, Email: {row[1]}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(get_users())
