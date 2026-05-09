
import asyncio
import uuid
import os
import sys

# Setup Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(ROOT_DIR)
for s in ["auth_service", "master_data_service", "inventory_service"]:
    sys.path.append(os.path.join(ROOT_DIR, s))

from common.infrastructure.database import AsyncSessionLocal
from master_app.models.product import Product
from master_app.models.warehouse import Warehouse
from master_app.models.location import InventoryLocation
from sqlalchemy import select

async def inject_product():
    async with AsyncSessionLocal() as session:
        # 1. Check if product exists
        result = await session.execute(select(Product).where(Product.sku == 'ECM-600'))
        product = result.scalar_one_or_none()
        
        company_id = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
        
        if not product:
            print("Creating Product ECM-600...")
            product = Product(
                id=uuid.uuid4(),
                company_id=company_id,
                name="Engine Control Module (ECM)",
                sku="ECM-600",
                description="Unidad de control de motor industrial Bosch",
                is_active=True
            )
            session.add(product)
            await session.commit()
            print(f"Product created with ID: {product.id}")
        else:
            print(f"Product ECM-600 already exists (ID: {product.id})")
            
        # 2. Ensure price/variant is reachable (Simulated via simple product for POS)
        # Note: The POS currently looks up in the Product table.
        
inject_product_script = inject_product()
asyncio.run(inject_product_script)
