import asyncio
import sys
import os

# Add paths to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))
sys.path.append(os.path.join(os.getcwd(), "backend", "master_data_service"))

from app.core.database import engine
from app.models.warehouse import Warehouse
from sqlalchemy import select

async def dump():
    async with engine.connect() as conn:
        stmt = select(Warehouse)
        result = await conn.execute(stmt)
        warehouses = result.fetchall()
        
        print(f"{'ID':<40} | {'CODE':<15} | {'NAME':<30} | {'COMPANY_ID':<40}")
        print("-" * 135)
        for w in warehouses:
            print(f"{str(w.id):<40} | {str(w.code):<15} | {str(w.name):<30} | {str(w.company_id):<40}")

if __name__ == "__main__":
    asyncio.run(dump())
