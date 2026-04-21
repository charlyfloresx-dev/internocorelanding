import asyncio
import uuid
import os
import sys

# Add current path to sys.path
sys.path.append(os.getcwd())

from master_app.db.session import AsyncSessionLocal
from master_app.models.product_category import ProductCategory
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ProductCategory))
        categories = res.scalars().all()
        print("CATEGORIES IN DB:")
        for c in categories:
            print(f"- {c.code}: {c.name} (ID: {c.id}, Company: {c.company_id})")

if __name__ == "__main__":
    asyncio.run(check())

