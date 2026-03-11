import asyncio
import uuid
import sys
import os

# Setup path
sys.path.append(os.path.join(os.getcwd(), "backend", "inventory_service"))

from app.db.session import AsyncSessionLocal
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository

# Demo IDs
CO_LOGISTICS_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
FAKE_COMPANY_ID = uuid.uuid4()

async def test_leak():
    print(f"🚀 Starting Tenant Leak Test...")
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyInventoryRepository(session)
        
        # 1. Query with Demo Company ID
        demo_stock = await repo.get_dashboard_stock(CO_LOGISTICS_ID)
        print(f"📦 Demo Company Stock Items: {len(demo_stock)}")
        if len(demo_stock) == 0:
            print("❌ Error: Demo stock not found. Seed might have failed.")
            return

        # 2. Query with FAKE Company ID
        fake_stock = await repo.get_dashboard_stock(FAKE_COMPANY_ID)
        print(f"🛡️ Fake Company Stock Items: {len(fake_stock)}")
        
        if len(fake_stock) > 0:
            print("🚨 LEAK DETECTED! Fake company can see stock items.")
        else:
            print("✅ PASS: No stock leak detected for unauthorized company.")

if __name__ == "__main__":
    asyncio.run(test_leak())
