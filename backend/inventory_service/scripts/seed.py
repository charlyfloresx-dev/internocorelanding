import asyncio
import uuid
import logging
import os
import sys
import random
import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import text, select

# Path Normalization
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from app.db.session import AsyncSessionLocal
from app.models.inventory import InventoryLevel
from app.models.concept import MovementConcept
from app.models.item_variant import ItemVariant
from app.models.movement import Movement
from app.models.customs_pedimento import CustomsPedimento, CustomsOperationType
from app.models.document import InventoryDocument, DocumentStatus
from app.models.warehouse import Warehouse
from app.models.warehouse import Warehouse

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_inventory")

async def seed_inventory(company_id: uuid.UUID):
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.now(timezone.utc)
            SYSTEM_USER_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
            UOM_PZ_ID      = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")
            
            logger.info(f"🌱 [INVENTORY] Iniciando seed blindado determinista (Rectificado) para {company_id}")

            # 1. Almacenes (Independiente)
            wh_codes = ["WH-TIJ", "WH-SDY"]
            wh_map = {}
            for code in wh_codes:
                wh_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_id}.{code}")
                wh_map[code] = wh_id
                res = await session.execute(select(Warehouse).where(Warehouse.id == wh_id))
                if not res.scalar():
                    session.add(Warehouse(
                        id=wh_id, company_id=company_id, tenant_id=company_id,
                        code=code, name=f"Warehouse {code}", is_active=True
                    ))

            # --- 2. PRODUCTOS (FUERA DE CUALQUIER BUCLE DE ALMACÉN) ---
            skus = ["PIZZA-BOX-01", "BOX-INDUSTRIAL-44"]
            variant_map = {}
            for sku in skus:
                v_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"variant.{company_id}.{sku}")
                p_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"item.{company_id}.{sku}")
                variant_map[sku] = (v_id, p_id)
                
                v_res = await session.execute(select(ItemVariant).where(ItemVariant.id == v_id))
                if not v_res.scalar():
                    logger.info(f"[+] SEEDING_VARIANT: SKU={sku}, ID={v_id}")
                    session.add(ItemVariant(
                        id=v_id, company_id=company_id, tenant_id=company_id,
                        product_id=p_id, internal_sku=sku, is_active=True, created_by=SYSTEM_USER_ID,
                        brand="INDUSTRIAL-CORP", mfg_part_number=f"MPN-{sku}"
                    ))
                else:
                    logger.warning(f"[!] VARIANT_ALREADY_EXISTS: ID={v_id}. Skipping.")
                
                # Nivel de stock determinista (Solo en TIJ para esta prueba)
                lvl_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"stock.{wh_map['WH-TIJ']}.{v_id}")
                lvl_res = await session.execute(select(InventoryLevel).where(InventoryLevel.id == lvl_id))
                if not lvl_res.scalar():
                    session.add(InventoryLevel(
                        id=lvl_id, company_id=company_id, tenant_id=company_id,
                        warehouse_id=wh_map["WH-TIJ"], product_id=p_id, uom_id=UOM_PZ_ID,
                        quantity=Decimal("500.0"), is_active=True, created_by=SYSTEM_USER_ID
                    ))

            # 3. Transacciones FIFO (Lotes con IDs fijos)
            for i in range(1, 4):
                sku = skus[i % len(skus)]
                v_id, p_id = variant_map[sku]
                ped_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"ped.{company_id}.{i}")
                p_number = f"PED-{str(company_id)[:4]}-{i}"
                
                ped_res = await session.execute(select(CustomsPedimento).where(CustomsPedimento.id == ped_id))
                if not ped_res.scalar():
                    session.add(CustomsPedimento(
                        id=ped_id, company_id=company_id, tenant_id=company_id,
                        pedimento_number=p_number, customs_key="IM", is_active=True,
                        operation_type=CustomsOperationType.IMPORT,
                        customs_date=(now - timedelta(days=20)).replace(tzinfo=None), created_by=SYSTEM_USER_ID
                    ))
                
                doc_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"doc.{company_id}.{i}")
                doc_res = await session.execute(select(InventoryDocument).where(InventoryDocument.id == doc_id))
                if not doc_res.scalar():
                    session.add(InventoryDocument(
                        id=doc_id, company_id=company_id, tenant_id=company_id,
                        folio=f"FOL-{str(company_id)[:4]}-{i}", document_type="ENTRY", is_active=True,
                        status=DocumentStatus.PROCESSED, origin_name="Supplier", 
                        external_reference=f"REF-{str(company_id)[:4]}-{i}", created_by=SYSTEM_USER_ID
                    ))
                
                mov_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"mov.{company_id}.{i}")
                mov_res = await session.execute(select(Movement).where(Movement.id == mov_id))
                if not mov_res.scalar():
                    session.add(Movement(
                        id=mov_id, company_id=company_id, tenant_id=company_id,
                        warehouse_id=wh_map["WH-TIJ"], product_id=p_id, quantity=Decimal("100.0"),
                        available_quantity=Decimal("100.0"), uom_id=UOM_PZ_ID, weight=Decimal("1.0"),
                        movement_type="IN", document_type="ENTRY", document_id=doc_id, 
                        customs_pedimento_id=ped_id, location=f"RACK-{i}", is_active=True,
                        created_by=SYSTEM_USER_ID
                    ))

            await session.commit()
            logger.info("✅ SUCCESS: Datos FIFO deterministas inyectados con arquitectura rectificada.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ ERROR: {str(e)}")
            raise

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--wipe", action="store_true")
    args = parser.parse_args()
    cid = uuid.UUID(args.company_id)
    if args.wipe:
        async with AsyncSessionLocal() as session:
            logger.info("🧹 Atomic Wipe...")
            tabs = ["inventory_movements", "inventory_levels", "inventory_documents", 
                    "inventory_item_variants", "inventory_warehouses", "customs_pedimentos"]
            for tab in tabs:
                await session.execute(text(f"TRUNCATE TABLE {tab} CASCADE"))
            await session.commit()
    await seed_inventory(cid)

if __name__ == "__main__":
    asyncio.run(main())
