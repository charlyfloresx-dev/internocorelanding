import asyncio
import os
import sys
import uuid
from decimal import Decimal

# Ensure backend and common are in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from common.config import settings
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository

# Mock Company ID (Logistic from seed)
LOGISTIC_COMPANY_ID = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

async def test_search():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        repo = SQLAlchemyInventoryRepository(session)
        
        print("\n--- Testing Search by SKU: 'MAT-001' ---")
        results = await repo.search_items_and_variants("MAT-001", LOGISTIC_COMPANY_ID)
        for r in results:
            print(f"Match: {r['display_name']}")
            print(f"   Stock: {r['quantity']} | Weight: {r['weight']} | Volume: {r['volume']}")
        
        print("\n--- Testing Search by Brand: 'Alcoa' ---")
        results = await repo.search_items_and_variants("Alcoa", LOGISTIC_COMPANY_ID)
        for r in results:
            print(f"Match: {r['display_name']}")

        print("\n--- Testing Search by MPN: 'AL-6061' ---")
        results = await repo.search_items_and_variants("AL-6061", LOGISTIC_COMPANY_ID)
        for r in results:
            print(f"Match: {r['display_name']}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_search())
