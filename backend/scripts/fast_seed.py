import asyncio
import uuid
import logging
import os
import sys
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Path Normalization
sys.path.append(os.getcwd())

from inventory_service.app.db.session import AsyncSessionLocal
from inventory_service.app.models.inventory import InventoryLevel
from inventory_service.app.models.item_variant import ItemVariant
from inventory_service.app.models.movement import Movement
from inventory_service.app.models.document import InventoryDocument, DocumentStatus
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed")

async def run():
    async with AsyncSessionLocal() as session:
        try:
            logger.info("CLEANUP")
            await session.execute(text("TRUNCATE TABLE inventory_movements, inventory_levels, inventory_documents, inventory_item_variants CASCADE"))
            await session.commit()
            
            CO_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
            UOM_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZ")
            
            skus = [f"SKU-{i}" for i in range(10)]
            whs = [uuid.uuid4() for _ in range(5)]
            
            for sku in skus:
                pid = uuid.uuid5(uuid.NAMESPACE_DNS, sku)
                session.add(ItemVariant(company_id=CO_ID, product_id=pid, internal_sku=sku, brand="PRO", mfg_part_number=sku, unit_price=10))
                for wh in whs:
                    session.add(InventoryLevel(company_id=CO_ID, warehouse_id=wh, product_id=pid, uom_id=UOM_ID, quantity=100))
            
            for i in range(20):
                did = uuid.uuid4()
                session.add(InventoryDocument(id=did, company_id=CO_ID, folio=f"DOC-{i}", document_type="ENTRY", status=DocumentStatus.PROCESSED, origin_name="A", destination_name="B"))
                session.add(Movement(company_id=CO_ID, warehouse_id=whs[0], product_id=uuid.uuid5(uuid.NAMESPACE_DNS, "SKU-0"), quantity=1, uom_id=UOM_ID, weight=1, movement_type="IN", document_type="ENT", document_id=did))
                
            await session.commit()
            logger.info("DONE")
        except Exception as e:
            logger.error(f"FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(run())
