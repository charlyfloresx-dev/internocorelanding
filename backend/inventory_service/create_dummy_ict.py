import asyncio
import uuid
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def create_dummy_ict():
    async with AsyncSessionLocal() as db:
        # Get a product from inventory levels (avoids 'products' table issue)
        res = await db.execute(text("SELECT product_id, warehouse_id FROM inventory_levels LIMIT 1"))
        data = res.fetchone()
        if not data:
            print("No inventory levels found to create ICT.")
            return

        product_id = data[0]
        warehouse_id = data[1]

        folio = "ICT-TEST-50"
        ict_id = uuid.uuid4()
        enterprise_id = "9cd9986b-89da-48b7-8733-26a2a1225b01"
        logistics_id = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"
        
        # Clean previous attempt
        await db.execute(text("DELETE FROM inter_company_transfers WHERE folio = :f"), {"f": folio})

        await db.execute(text("""
            INSERT INTO inter_company_transfers (
                id, folio, product_id, origin_sku, quantity, weight, currency,
                origin_warehouse_id, destination_warehouse_id, transit_warehouse_id, 
                status, company_id, tenant_id, version_id, is_active,
                created_at, created_by, destination_company_id, uom_id,
                pending_financial_valuation
            ) VALUES (
                :id, :folio, :pid, 'SKU-DUMMY', 10.0, 0.0, 'USD',
                :wh, :wh, :wh,
                'PENDING', :oid, :oid, 1, true,
                now(), :oid, :did, :wh,
                false
            )
        """), {
            "id": ict_id, "folio": folio, "pid": product_id,
            "wh": warehouse_id, "oid": enterprise_id, "did": logistics_id
        })
        await db.commit()
        print(f"Created cross-company ICT: {folio} (From Enterprise to Logistics)")

if __name__ == "__main__":
    asyncio.run(create_dummy_ict())
