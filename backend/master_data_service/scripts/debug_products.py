import asyncio
import uuid
from app.db.db import async_session
from app.models.product import Product
from sqlalchemy import select

async def run():
    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()
        print(f"Total products: {len(products)}")
        for p in products:
            print(f"SKU: {p.sku} | ID: {p.id} | Company: {p.company_id}")

if __name__ == "__main__":
    asyncio.run(run())
