import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://user:password@localhost:5433/viatra_db')
    async with engine.connect() as conn:
        res_p = await conn.execute(text('SELECT count(*) FROM viatra_travel_packages'))
        res_g = await conn.execute(text('SELECT count(*) FROM viatra_traveler_groups'))
        print(f"Packages: {res_p.scalar()}")
        print(f"Groups: {res_g.scalar()}")

if __name__ == "__main__":
    asyncio.run(check())
