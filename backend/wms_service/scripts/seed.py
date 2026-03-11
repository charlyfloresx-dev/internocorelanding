import asyncio
import argparse
import uuid
import logging
import os
import sys
from datetime import datetime, timezone

# Ajuste de path para encontrar 'app' y 'common'
sys.path.append(os.getcwd())

from sqlalchemy.future import select
from app.core.database import engine, AsyncSessionLocal as SessionLocal 

# IMPORTANTE: Importar todos los modelos para que Base.metadata esté poblado
import app.models 
from common.models import Base, MultiTenantBase
from app.models.warehouse import Warehouse, Zone
from app.models.location import Location, LocationType
from app.models.concept import Concept, ConceptType
from app.models.item import Item 
from app.models.product import Product
from app.models.product_price import ProductPrice, PriceType, PriceOriginType

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_wms")

# --- CONSTANTES ---
CO_LOGISTICS_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
SYSTEM_USER_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38") # Admin "Charly"

async def seed_concepts(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando conceptos para company: {company_id}")
    concepts = [
        ("ENT", "Entrada por Compra", ConceptType.ENTRY),
        ("SAL", "Salida por Venta", ConceptType.OUTPUT),
        ("AJU", "Ajuste de Inventario", ConceptType.ADJUSTMENT),
        ("TRA", "Transferencia", ConceptType.TRANSFER),
    ]
    for code, name, c_type in concepts:
        stmt = select(Concept).filter_by(company_id=company_id, code=code)
        result = await db.execute(stmt)
        if not result.scalars().first():
            db.add(Concept(
                id=uuid.uuid4(),
                company_id=company_id,
                code=code,
                name=name,
                concept_type=c_type,
                affect_stock=True,
                created_by=SYSTEM_USER_ID
            ))

async def seed_warehouses(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando almacenes para company: {company_id}")
    whs = [
        ("WH-TIJ", "Almacen Tijuana"),
        ("WH-SDY", "Almacen San Diego"),
    ]
    for code, name in whs:
        wh_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wh.{code}.{company_id}")
        existing = await db.get(Warehouse, wh_id)
        if not existing:
            db.add(Warehouse(
                id=wh_id,
                company_id=company_id,
                code=code,
                name=name,
                capacity=10000.0,
                is_active=True,
                created_by=SYSTEM_USER_ID
            ))

async def seed_items(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando catálogo de items para company: {company_id}")
    # MAT-001 al MAT-010 (Alineado con Inventory Seed)
    for i in range(1, 11):
        sku = f"MAT-{str(i).zfill(3)}"
        item_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{sku}")
        existing = await db.get(Item, item_id)
        if not existing:
            db.add(Item(
                id=item_id,
                company_id=company_id,
                code=sku,
                name=f"Material Demo {sku}",
                active=True,
                created_by=SYSTEM_USER_ID
            ))

async def seed_prices(db, company_id: uuid.UUID):
    logger.info(f"  [WMS] Cargando matriz de precios para company: {company_id}")
    wh_tij_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.wh.WH-TIJ.{company_id}")
    
    # Escenarios para el Demo:
    # SKU-100 (MAT-001): General $100 | Tijuana $120
    # SKU-200 (MAT-002): General $60  | Tijuana $45 (Liquidación)
    price_configs = [
        ("MAT-001", wh_tij_id, 100.0, PriceType.SALE, "Precio Premium Frontera"),
        ("MAT-001", None, 100.0, PriceType.SALE, "Precio Base Nacional"),
        ("MAT-002", wh_tij_id, 45.0, PriceType.SALE, "Liquidación Local"),
        ("MAT-002", None, 60.0, PriceType.SALE, "Precio Nacional"),
    ]

    for sku, wh_id, sale, p_type, justif in price_configs:
        prod_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{sku}")
        price_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"price.{sku}.{wh_id or 'GENERAL'}.{company_id}")
        
        existing = await db.get(ProductPrice, price_id)
        if not existing:
            db.add(ProductPrice(
                id=price_id,
                company_id=company_id,
                product_id=prod_id,
                warehouse_id=wh_id,
                amount=sale,
                price_type=p_type,
                version=1,
                change_reason=justif,
                origin_type=PriceOriginType.SEED,
                justification=justif,
                is_active=True,
                created_by=SYSTEM_USER_ID,
                start_date=datetime.now(timezone.utc)
            ))

async def main(company_id: uuid.UUID):
    async with SessionLocal() as db:
        try:
            logger.info(f"🌱 [WMS] Iniciando Seeding para company: {company_id}")
            
            # Garantizar tablas completas (Agresivo para Demo: drop de tablas conflictivas)
            async with engine.begin() as conn:
                # Opcional: solo si estamos seguros de que podemos borrar datos
                # await conn.run_sync(Base.metadata.drop_all) # Demasiado destructivo?
                # Vamos a borrar solo las que sabemos que cambiaron significativamente
                from sqlalchemy import text
                await conn.execute(text("DROP TABLE IF EXISTS product_prices CASCADE;"))
                await conn.execute(text("DROP TABLE IF EXISTS items CASCADE;"))
                await conn.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
                await conn.execute(text("DROP TABLE IF EXISTS sales_orders CASCADE;"))
                
                await conn.run_sync(Base.metadata.create_all)
            
            await seed_concepts(db, company_id)
            await seed_warehouses(db, company_id)
            await seed_items(db, company_id)
            await seed_prices(db, company_id)
            await db.commit()
            logger.info("✅ Seeding WMS completado.")
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Error en seeding WMS: {e}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", default=str(CO_LOGISTICS_ID))
    args = parser.parse_args()
    asyncio.run(main(company_id=uuid.UUID(args.company_id)))
