
import asyncio
import uuid
from sqlalchemy import select
from common.infrastructure.database import engine
from inventory_app.models.warehouse import Warehouse

async def check_warehouses():
    async with engine.connect() as conn:
        stmt = select(Warehouse)
        result = await conn.execute(stmt)
        warehouses = result.fetchall()
        print(f"Total warehouses in inventory DB: {len(warehouses)}")
        for w in warehouses:
            print(f"ID: {w.id}, Code: {w.code}, Company: {w.company_id}")

if __name__ == "__main__":
    asyncio.run(check_warehouses())
