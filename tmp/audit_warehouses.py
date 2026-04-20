import asyncio
import os
import sys
import uuid
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

# Path adjustment
CURRENT_DIR = os.getcwd() # c:\API\interno
BACKEND_DIR = os.path.join(CURRENT_DIR, "backend") # c:\API\interno\backend
sys.path.append(BACKEND_DIR)
sys.path.append(os.path.join(BACKEND_DIR, "master_data_service"))

from common.models import MultiTenantBase
from app.models.warehouse import Warehouse

async def check_warehouses():
    db_url = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
    engine = create_async_engine(db_url)
    
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
