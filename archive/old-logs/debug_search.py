import asyncio
import os
import sys
import uuid
from decimal import Decimal

# Ensure backend and common are in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend/inventory_service")))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_, and_
from common.config import settings
from app.models.item_variant import ItemVariant
from app.models.stock import Stock
from app.models.warehouse import Warehouse

# Mock Company ID (Logistic from seed)
LOGISTIC_COMPANY_ID = uuid.UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479")

async def test_debug():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("--- Step 1: Basic select on ItemVariant ---")
        try:
            stmt = select(ItemVariant).where(ItemVariant.company_id == LOGISTIC_COMPANY_ID).limit(1)
            res = await session.execute(stmt)
            print("Success")
        except Exception as e:
            print(f"Failed Step 1: {e}")

        print("\n--- Step 2: Join ItemVariant and Stock ---")
        try:
            stmt = select(ItemVariant, Stock).join(Stock, Stock.product_id == ItemVariant.product_id).where(ItemVariant.company_id == LOGISTIC_COMPANY_ID).limit(1)
            res = await session.execute(stmt)
            print("Success")
        except Exception as e:
            print(f"Failed Step 2: {e}")

        print("\n--- Step 3: Full Search Query ---")
        try:
            search_query = "%MAT-001%"
            stmt = (
                select(
                    ItemVariant.id,
                    Stock.quantity,
                    Warehouse.name
                )
                .join(Stock, Stock.product_id == ItemVariant.product_id)
                .join(Warehouse, Warehouse.id == Stock.warehouse_id)
                .where(
                    and_(
                        ItemVariant.company_id == LOGISTIC_COMPANY_ID,
                        or_(
                            ItemVariant.internal_sku.ilike(search_query),
                            ItemVariant.mfg_part_number.ilike(search_query),
                            ItemVariant.brand.ilike(search_query)
                        )
                    )
                )
                .limit(10)
            )
            print(f"Generated SQL: {stmt}")
            res = await session.execute(stmt)
            print("Success")
        except Exception as e:
            print(f"Failed Step 3: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_debug())
