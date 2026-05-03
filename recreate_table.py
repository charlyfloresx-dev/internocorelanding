import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from inventory_app.models.location import InventoryLocation
from common.models import Base

async def recreate():
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/dbname")
    async with engine.begin() as conn:
        await conn.run_sync(InventoryLocation.metadata.create_all)
        print("Table created.")

asyncio.run(recreate())
