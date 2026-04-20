import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.product import Product
from common.config import settings

async def trigger_audit_event():
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost:5433/master_data_db")
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        # Find a product
        result = await session.execute(select(Product).limit(1))
        product = result.scalars().first()
        
        if product:
            print(f"Updating product: {product.name}")
            product.name = f"{product.name} (Audited)"
            product.weight_kg = 15.5
            await session.commit()
            print("Update committed.")
        else:
            print("No product found to update.")

if __name__ == "__main__":
    asyncio.run(trigger_audit_event())
