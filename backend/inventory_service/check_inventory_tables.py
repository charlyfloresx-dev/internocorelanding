import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://user:internocore_db_pass_2026@postgres-db:5432/inventory_db')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in res.fetchall()]
        print("TABLES IN INVENTORY_DB:", tables)
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
