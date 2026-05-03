import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from inventory_app.models.location import InventoryLocation
from common.models import Base
import uuid

async def test():
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/dbname")
    async with AsyncSession(engine) as session:
        loc = InventoryLocation(id=uuid.uuid4(), code="LOC-AUDIT-01", warehouse_id=uuid.uuid4(), company_id=uuid.uuid4(), tenant_id=uuid.uuid4(), group_id=uuid.uuid4())
        session.add(loc)
        try:
            await session.commit()
            print("Success")
        except Exception as e:
            print(f"Error: {e}")

asyncio.run(test())
