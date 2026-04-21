
import asyncio
from sqlalchemy import select
from master_app.db.db import async_session
from master_app.models.warehouse import Warehouse

async def check():
    async with async_session() as session:
        result = await session.execute(select(Warehouse.company_id).distinct())
        ids = [str(x) for x in result.scalars().all()]
        print("\n".join(ids))

if __name__ == "__main__":
    asyncio.run(check())
