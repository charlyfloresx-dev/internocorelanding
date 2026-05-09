
import asyncio
import uuid
import os
import sys
from decimal import Decimal

# Setup Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(ROOT_DIR)
for s in ["auth_service", "master_data_service", "inventory_service"]:
    sys.path.append(os.path.join(ROOT_DIR, s))

from common.infrastructure.database import AsyncSessionLocal
from master_app.models.product import Product
from inventory_app.models.item_variant import ItemVariant
from sqlalchemy import select

async def inject_variant():
    async with AsyncSessionLocal() as session:
        company_id = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
        product_id = uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000001")
        
        # 1. Ensure Product exists
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            print("Creating Base Product...")
            product = Product(
                id=product_id,
                company_id=company_id,
                name="Engine Control Module (ECM)",
                sku="ECM-BASE",
                is_active=True
            )
            session.add(product)
            await session.commit()

        # 2. Check if variant exists
        result = await session.execute(select(ItemVariant).where(ItemVariant.internal_sku == 'ECM-600'))
        variant = result.scalar_one_or_none()
        
        if not variant:
            print("Creating Variant ECM-600...")
            variant = ItemVariant(
                id=uuid.uuid4(),
                company_id=company_id,
                product_id=product_id,
                internal_sku="ECM-600",
                brand="Bosch",
                mfg_part_number="MPN-BOS-601",
                unit_price=Decimal("450.00"),
                is_preferred=True
            )
            session.add(variant)
            await session.commit()
            print(f"Variant created with ID: {variant.id}")
        else:
            print(f"Variant ECM-600 already exists (ID: {variant.id})")
            
inject_variant_script = inject_variant()
asyncio.run(inject_variant_script)
