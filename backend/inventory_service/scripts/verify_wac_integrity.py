# backend/inventory_service/scripts/verify_wac_integrity.py
import os
import sys
import uuid
import asyncio
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add /app and /app/inventory_service to path
sys.path.append("/app")
sys.path.append("/app/inventory_service")

from app.db.session import AsyncSessionLocal
from app.models.inventory import InventoryLevel

# Constants from Seed
WH_SDY_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.WH-SDY")
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
PROD_ALU_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.item.MAT-001")

async def verify():
    print("--- INITIATING WAC INTEGRITY AUDIT ---")
    print(f"Target Warehouse: SD Hub ({WH_SDY_ID})")
    print(f"Target Company: InternoCorp Enterprise ({CO_ENTERPRISE_ID})")
    print(f"Target Product: MAT-001 ({PROD_ALU_ID})")
    
    async with AsyncSessionLocal() as session:
        query = select(InventoryLevel).where(
            InventoryLevel.warehouse_id == WH_SDY_ID,
            InventoryLevel.product_id == PROD_ALU_ID,
            InventoryLevel.company_id == CO_ENTERPRISE_ID
        )
        result = await session.execute(query)
        level = result.scalar_one_or_none()
        
        if not level:
            print("❌ ERROR: Inventory Level for Empresa B not found in SD Hub.")
            return

        # 2. Extract values
        qty = level.quantity
        wac_amount = level.wac.amount if level.wac else Decimal("0.0")
        
        # 3. Expected Values:
        # Before seed: 50u @ 10.00
        # Received: 100u @ 25.00
        # Formula: ((50*10) + (100*25)) / 150 = 20.00
        
        expected_qty = Decimal("150.0")
        expected_wac = Decimal("20.0000")
        
        print(f"\nAudit Log:")
        print(f"  Current Qty: {qty} (Expected: {expected_qty})")
        print(f"  Current WAC: {wac_amount} (Expected: {expected_wac})")
        
        # 4. Precision Assertions
        qty_match = round(qty, 4) == round(expected_qty, 4)
        wac_match = round(wac_amount, 4) == round(expected_wac, 4)
        
        if qty_match and wac_match:
            print("\n✅ SUCCESS: Financial integrity verified. WAC matches mathematical model.")
        else:
            if not qty_match:
                print(f"❌ QUANTITY MISMATCH: Got {qty}, Expected {expected_qty}")
            if not wac_match:
                print(f"❌ WAC MISMATCH: Got {wac_amount}, Expected {expected_wac}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(verify())
