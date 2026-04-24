import asyncio
import uuid
from sqlalchemy import text
from common.infrastructure.database import engine

async def check_ids():
    ids = {
        "concept": "9dbdb03f-9f62-5d6b-b4e2-455f053f9bf4",
        "warehouse": "fd76bbe3-6d6f-5e74-ae15-d605acbc2289",
        "product": "e0e0e0e0-e0e0-40e0-a0e0-000000000001"
    }
    
    async with engine.connect() as conn:
        print("[*] Checking IDs in database...")
        
        # Check Warehouse
        res = await conn.execute(text("SELECT id FROM inventory_warehouses WHERE id = :id"), {"id": ids["warehouse"]})
        print(f"[-] Warehouse {ids['warehouse']}: {'FOUND' if res.fetchone() else 'NOT FOUND'}")
        
        # Check Concept
        res = await conn.execute(text("SELECT id FROM inventory_movement_concepts WHERE id = :id"), {"id": ids["concept"]})
        print(f"[-] Concept {ids['concept']}: {'FOUND' if res.fetchone() else 'NOT FOUND'}")
        
        # Check Product (ItemVariant)
        res = await conn.execute(text("SELECT id FROM inventory_item_variants WHERE id = :id"), {"id": ids["product"]})
        print(f"[-] Product {ids['product']}: {'FOUND' if res.fetchone() else 'NOT FOUND'}")

if __name__ == "__main__":
    asyncio.run(check_ids())
