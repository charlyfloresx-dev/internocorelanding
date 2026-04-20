import asyncio
import sys
import os

# Ensure the app module is found
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.product_category import ProductCategory
from app.models.product_brand import ProductBrand
from app.models.uom import UOM
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.movement_concept import MovementConcept
from app.core.events import setup_audit_listeners

async def test_audit():
    # Force registration just in case
    setup_audit_listeners(Product)
    
    engine = create_async_engine('postgresql+asyncpg://user:password@postgres-db:5432/master_data_db')
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Get a product
        res = await session.execute(select(Product).limit(1))
        p = res.scalars().first()
        if p:
            print(f"Found product: {p.name}")
            p.name = p.name[:240] + ' Audited'
            await session.commit()
            print("Product updated. Audit log should be generated.")
        else:
            print("No product found to update.")

if __name__ == "__main__":
    asyncio.run(test_audit())
