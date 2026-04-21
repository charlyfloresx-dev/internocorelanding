import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from inventory_app.db.session import AsyncSessionLocal

# Configuration
CO_LOGISTICS_ID  = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"
CO_ENTERPRISE_ID = "9cd9986b-89da-48b7-8733-26a2a1225b01"
CHARLY_ID        = "69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38"

WH_TIJ_ID     = "ad6cc8a6-34f9-42df-8f29-28254e0ad242" 
WH_SDY_ID     = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"  # Using existing id just in case
WH_TRANSIT_ID = "ad6cc8a6-34f9-42df-8f29-28254e0ad242" 
PROD_ALU_ID   = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"
UOM_PZ_ID     = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"

async def generate():
    folio = f"ICT-READY-{str(uuid.uuid4())[:6].upper()}"
    t_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    print(f"Generating Transfer {folio} via RAW SQL...")
    
    # We use some of the logistics company's IDs to avoid FK issues if they exist
    # But I checked they are not enforced. Still, let's use valid looking UUIDs.
    
    query = text("""
        INSERT INTO inter_company_transfers (
            id, folio, status, company_id, tenant_id, destination_company_id,
            origin_warehouse_id, destination_warehouse_id, transit_warehouse_id,
            product_id, uom_id, quantity, weight, currency,
            unit_price_at_dispatch, wac_at_dispatch, transfer_revenue_a,
            shipped_at, shipped_by, created_at, is_active, version_id
        ) VALUES (
            :id, :folio, :status, :company_id, :tenant_id, :destination_company_id,
            :origin_warehouse_id, :destination_warehouse_id, :transit_warehouse_id,
            :product_id, :uom_id, :quantity, :weight, :currency,
            :up, :wac, :rev,
            :shipped_at, :shipped_by, :created_at, :is_active, :version_id
        )
    """)
    
    params = {
        "id": t_id,
        "folio": folio,
        "status": "SHIPPED",
        "company_id": CO_ENTERPRISE_ID,
        "tenant_id": CO_ENTERPRISE_ID,
        "destination_company_id": CO_LOGISTICS_ID,
        "origin_warehouse_id": str(uuid.uuid4()),
        "destination_warehouse_id": str(uuid.uuid4()),
        "transit_warehouse_id": str(uuid.uuid4()),
        "product_id": str(uuid.uuid4()),
        "uom_id": str(uuid.uuid4()),
        "quantity": 50.0,
        "weight": 5.0,
        "currency": "USD",
        "up": 12.5,
        "wac": 10.0,
        "rev": 625.0,
        "shipped_at": now,
        "shipped_by": CHARLY_ID,
        "created_at": now,
        "is_active": True,
        "version_id": 1
    }
    
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(query, params)
            await session.commit()
            print(f"--- SUCCESS ---")
            print(f"FOLIO: {folio}")
            print(f"Destination: {CO_LOGISTICS_ID}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate())
