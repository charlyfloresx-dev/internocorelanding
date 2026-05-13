import asyncio
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

INV_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/inventory_db"
COMPANY_ID = "11111111-1111-4111-8111-123456789abc"
WH_ID = "aa11aaaa-aaaa-4aaa-8aaa-123456789abc"

async def check_or_create_location():
    engine = create_async_engine(INV_DB_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        # 1. Ensure location exists with small capacity
        try:
            res = await conn.execute(text("SELECT id FROM inventory_locations WHERE code = 'BIN-STRESS-01' AND company_id = :cid"), {"cid": COMPANY_ID})
            row = res.fetchone()
            
            if not row:
                print("[STRESS] Creating location BIN-STRESS-01 with max_capacity=10")
                await conn.execute(text("""
                    INSERT INTO inventory_locations (id, warehouse_id, code, max_capacity, company_id, tenant_id, is_active, version_id)
                    VALUES (gen_random_uuid(), :wh, 'BIN-STRESS-01', 10, :cid, :cid, true, 1)
                """), {"wh": WH_ID, "cid": COMPANY_ID})
            else:
                print("[STRESS] Setting BIN-STRESS-01 max_capacity=10")
                await conn.execute(text("UPDATE inventory_locations SET max_capacity = 10 WHERE code = 'BIN-STRESS-01' AND company_id = :cid"), {"cid": COMPANY_ID})
        except Exception as e:
            print(f"Error: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_or_create_location())
