import asyncio
import uuid
import sys
import os

# Add /app and /app/common to path if needed, but within Docker /app is enough
sys.path.append("/app")

from inventory_app.api.v1.handlers.readiness_handler import GetCompanyInventoryReadinessHandler, GetCompanyInventoryReadinessQuery
from inventory_app.db.session import AsyncSessionLocal
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.infrastructure.clients.master_data import MasterDataClient

async def test():
    print("🚀 Starting Diagnostic Tool for Readiness...")
    company_id = uuid.UUID('9cd9986b-89da-48a3-9eb7-873326a2a122') # InternoCorp Enterprise
    
    # 1. Manually instantiate dependencies to avoid DI complexities in one-off script
    db = AsyncSessionLocal()
    md_client = MasterDataClient()
    repo = SQLAlchemyInventoryRepository(db, md_client)
    
    handler = GetCompanyInventoryReadinessHandler(repo, md_client)
    query = GetCompanyInventoryReadinessQuery(company_id=company_id)
    
    try:
        print(f"Executing handler for {company_id}...")
        res = await handler.handle(query)
        print(f"✅ Result: {res}")
    except Exception as e:
        print(f"❌ DEADLY EXCEPTION in Readiness Handler: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test())
