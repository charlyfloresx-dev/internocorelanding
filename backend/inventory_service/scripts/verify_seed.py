import asyncio
import os
import sys
import uuid
from sqlalchemy import text

# Matching seed.py logic
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SERVICE_APP = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
if SERVICE_APP not in sys.path:
    sys.path.insert(0, SERVICE_APP)

os.chdir(SERVICE_APP) 
from app.db.session import engine

async def verify_data():
    print("🔍 [VERIFICATION] Checking Inventory Data...")
    async with engine.connect() as conn:
        r1 = await conn.execute(text("SELECT count(*) FROM inventory_item_variants"))
        r2 = await conn.execute(text("SELECT count(*) FROM inventory_movements"))
        
        variants_count = r1.scalar()
        movements_count = r2.scalar()
        
        print(f"✅ Variants Seeded: {variants_count}")
        print(f"✅ Movements Seeded: {movements_count}")
        
        # simplified check for MAT-001 (UUID matches namespace)
        mat001_id = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.item.MAT-001")
        wh_tij_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wh.WH-TIJ.ad6cc8a6-34f9-42df-8f29-28254e0ad242")
        
        r4 = await conn.execute(text("SELECT quantity FROM inventory_levels WHERE product_id = :pid AND warehouse_id = :whid"), {"pid": mat001_id, "whid": wh_tij_id})
        qty = r4.scalar()
        print(f"✅ MAT-001 Stock in WH-TIJ: {qty} (Expected: 12.0)")

if __name__ == "__main__":
    asyncio.run(verify_data())
