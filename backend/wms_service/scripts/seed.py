import asyncio
import argparse
import uuid
import logging
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

# Ajuste de path
sys.path.append(os.getcwd())

from sqlalchemy.future import select
from app.core.database import engine, AsyncSessionLocal as SessionLocal 

from app.models.item import Item
from app.models.concept import Concept
from app.models.warehouse import Warehouse
from app.models.product_price import ProductPrice, PriceType, PriceOriginType
from app.models.price_agreement import PriceAgreement, AgreementType
from common.enums import WarehouseType, MovementType

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_wms")

# IDs Homologados
LOGISTICS_ID   = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
SYSTEM_USER_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

async def seed_concepts(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando conceptos para company: {company_id}")
    concepts = [
        ("ENT", "Entrada por Compra", MovementType.ENTRY),
        ("SAL", "Salida por Venta", MovementType.OUTPUT),
        ("AJU", "Ajuste de Inventario", MovementType.ADJUSTMENT),
        ("TRA", "Transferencia", MovementType.TRANSFER),
    ]
    for code, name, c_type in concepts:
        stmt = select(Concept).filter_by(company_id=company_id, code=code)
        result = await db.execute(stmt)
        if not result.scalars().first():
            db.add(Concept(
                id=uuid.uuid4(), company_id=company_id, tenant_id=company_id,
                code=code,
                name=name, type=c_type, affect_stock=True,
                created_by=SYSTEM_USER_ID
            ))

async def seed_warehouses(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando almacenes para company: {company_id}")
    wh_codes = ["WH-TIJ", "WH-SDY", "WH-ENS", "WH-OTY"]
    for code in wh_codes:
        wh_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_id}.{code}")
        existing = await db.get(Warehouse, wh_id)
        if not existing:
            db.add(Warehouse(
                id=wh_id, company_id=company_id, tenant_id=company_id,
                code=code,
                name=f"WMS {code} - {company_id.hex[:4]}",
                type=WarehouseType.PHYSICAL,
                country_code="MX",
                capacity=10000.0, is_active=True, created_by=SYSTEM_USER_ID
            ))

async def seed_items(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando catálogo de items para company: {company_id}")
    for i in range(1, 11):
        sku = f"MAT-{str(i).zfill(3)}"
        
        # 💡 IDENTIDAD INDUSTRIAL GLOBAL
        # El master_product_id es el mismo para todo el grupo basado solo en el SKU
        master_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.master.product.{sku}")
        
        # El ID local del item en WMS sigue siendo único por empresa para evitar colisiones
        item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wms.item.{company_id}.{sku}")
        
        existing = await db.get(Item, item_id)
        if not existing:
            db.add(Item(
                id=item_id, 
                company_id=company_id, 
                tenant_id=company_id,
                master_product_id=master_id, # 🔗 Vínculo global
                code=sku,
                sku=sku,
                name=f"Material Industrial {sku}",
                is_active=True,
                created_by=SYSTEM_USER_ID,
                stock_quantity=Decimal("0.0"),
                status="ACTIVE"
            ))

async def seed_prices(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando Acuerdos y Precios para company: {company_id}")
    
    # 1. Crear Acuerdo Global
    agreement_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.agreement.{company_id}.GLOBAL")
    existing_agreement = await db.get(PriceAgreement, agreement_id)
    if not existing_agreement:
        db.add(PriceAgreement(
            id=agreement_id, company_id=company_id, tenant_id=company_id,
            name="Lista de Precios Global",
            agreement_type=AgreementType.GLOBAL,
            is_active=True, created_by=SYSTEM_USER_ID
        ))
        await db.flush()
    
    # 2. Sembrar precios para los 10 items
    for i in range(1, 11):
        sku = f"MAT-{str(i).zfill(3)}"
        # Sincronizado con seed_items (Identidad Industrial)
        item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wms.item.{company_id}.{sku}")
        
        # Precio Nivel 1 (Base)
        price_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.price.{agreement_id}.{sku}.v1")
        existing_price = await db.get(ProductPrice, price_id)
        if not existing_price:
            db.add(ProductPrice(
                id=price_id, company_id=company_id, tenant_id=company_id,
                product_id=item_id,
                agreement_id=agreement_id,
                price_type=PriceType.LIST,
                _amount=Decimal(100.0 + i),
                _currency="USD",
                version=1,
                change_reason="Carga Inicial Seed",
                origin_type=PriceOriginType.SEED,
                is_active=True,
                created_by=SYSTEM_USER_ID
            ))
    logger.info("  ✅ Precios de catálogo sembrados.")

async def main(company_id: uuid.UUID, wipe: bool):
    async with SessionLocal() as db:
        try:
            logger.info(f"🌱 [WMS] Iniciando Seeding para company: {company_id}")
            
            if wipe:
                async with engine.begin() as conn:
                    from sqlalchemy import text
                    logger.info("  [WMS] Resetting Tables...")
                    await conn.execute(text("DROP TABLE IF EXISTS product_prices, inventory_snapshots, locations, products, zones, warehouses, concepts CASCADE"))
                    from app.models import Base
                    await conn.run_sync(Base.metadata.create_all)
            
            await seed_concepts(db, company_id)
            await seed_warehouses(db, company_id)
            await seed_items(db, company_id)
            await seed_prices(db, company_id)
            await db.commit()
            logger.info(f"✅ [WMS] Seed {company_id} completado.")
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error en seeding WMS: {e}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", default=str(LOGISTICS_ID))
    parser.add_argument("--wipe", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(company_id=uuid.UUID(args.company_id), wipe=args.wipe))
