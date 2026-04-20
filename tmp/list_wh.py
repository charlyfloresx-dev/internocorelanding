
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_all_wh():
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/master_data_db")
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT id, name FROM warehouses"))
        for row in res.all():
            print(row)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_all_wh())
