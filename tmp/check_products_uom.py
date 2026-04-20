import asyncio
import uuid
from sqlalchemy import select, text
from app.db.session import SessionLocal, engine
from app.models.product import Product

async def check_products():
    async with SessionLocal() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        print(f"Total Products: {len(products)}")
        for p in products:
            print(f"SKU: {p.sku}, Name: {p.name}, UOM_ID: {p.base_uom_id}")

if __name__ == "__main__":
    import os
    import sys
    # Add project root to sys.path
    project_root = r"c:\API\interno\backend\master_data_service"
    sys.path.append(project_root)
    # Mock settings if needed or just use current ones
    asyncio.run(check_products())
