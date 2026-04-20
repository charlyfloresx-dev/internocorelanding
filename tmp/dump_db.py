import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_all():
    engine = create_async_engine('postgresql+asyncpg://user:password@localhost:5433/viatra_db')
    async with engine.connect() as conn:
        print("--- Packages ---")
        res = await conn.execute(text('SELECT id, name FROM viatra_travel_packages'))
        for r in res:
            print(r)
        
        print("--- Groups ---")
        res = await conn.execute(text('SELECT id, name FROM viatra_traveler_groups'))
        for r in res:
            print(r)

if __name__ == "__main__":
    asyncio.run(check_all())
