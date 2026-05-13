import asyncio
import sys
import os
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.getcwd())
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from common.domain import Base, ProductStatus
from master_app.models.product import Product
from master_app.db.session import DATABASE_URL

async def fix_corrupted_data():
    print("[Antigravity] Corrigiendo datos corruptos...")
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    
    async with engine.begin() as conn:
        # Corregir el estatus corrupto a ACTIVE
        result = await conn.execute(
            update(Base.metadata.tables["products"])
            .where(Base.metadata.tables["products"].c.status == "CORRUPTED_STATUS")
            .values(status=ProductStatus.ACTIVE.value)
        )
        print(f"  [OK] {result.rowcount} registro(s) corregido(s) a ACTIVE.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_corrupted_data())
