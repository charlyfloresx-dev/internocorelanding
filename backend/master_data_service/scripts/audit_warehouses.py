import asyncio
import os
import sys
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

# Path adjustment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from master_app.models.warehouse import Warehouse

async def check_warehouses():
    # Inside docker: postgres:5432
    # Outside docker: localhost:5433
    db_url = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
    engine = create_async_engine(db_url, pool_pre_ping=True)
    
    async with engine.connect() as conn:
        stmt = select(Warehouse)
        result = await conn.execute(stmt)
        rows = result.all()
        
        print(f"{'ID':<40} {'CODE':<15} {'NAME':<30} {'COMPANY_ID':<40}")
        print("-" * 125)
        for r in rows:
            print(f"{str(r.id):<40} {r.code:<15} {r.name:<30} {str(r.company_id):<40}")

if __name__ == "__main__":
    asyncio.run(check_warehouses())
