import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    urls = [
        "postgresql+asyncpg://user:password@localhost:5433/dbname",
    ]
    
    for url in urls:
        print(f"--- Checking {url} ---")
        try:
            engine = create_async_engine(url, pool_pre_ping=True)
            async with engine.connect() as conn:
                res = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"))
                tables = [row[0] for row in res]
                print(f"Tables: {tables}")
            await engine.dispose()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check())
