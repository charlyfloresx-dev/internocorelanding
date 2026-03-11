import asyncio
import argparse
import uuid
import logging
import os
import sys
from datetime import datetime, timezone

# Ajuste de path para encontrar 'app' y 'common'
sys.path.append(os.getcwd())

from app.db.db import async_session
from app.models.uom import UOM
from app.models.product import Product, ProductVersion
from common.enums import ProductStatus, VersionStatus, ProductType
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_master_data")

# --- CONSTANTES ---
CO_LOGISTICS_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000") # Identity Standard

async def seed_uoms(session):
    logger.info("  [MD] Cargando UOMs globales...")
    uoms_to_seed = [
        {"id": uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA"), "code": "PZ", "name": "Pieza", "plural": "Piezas"},
        {"code": "UN", "name": "Unidad", "plural": "Unidades"},
        {"code": "KG", "name": "Kilogramo", "plural": "Kilogramos"},
        {"code": "GL", "name": "Galón", "plural": "Galones"},
    ]
    
    for uom_data in uoms_to_seed:
        id_ = uom_data.get("id") or uuid.uuid5(uuid.NAMESPACE_DNS, f"uom.{uom_data['code']}")
        existing = await session.get(UOM, id_)
        if not existing:
            session.add(UOM(
                id=id_, company_id=None, code=uom_data["code"],
                name=uom_data["name"], plural=uom_data["plural"],
                is_active=True, version_id=1, created_by=SYSTEM_USER_ID
            ))
            logger.info(f"    ➕ UOM: {uom_data['code']}")
    await session.flush()

async def seed_demo_products(session, company_id: uuid.UUID):
    logger.info(f"  [MD] Cargando catálogo demo para company: {company_id}")
    uom_pz_id = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")
    
    items_def = [
        ("MAT-001", "Pallet Madera Estándar"),
        ("MAT-002", "Film Stretch 20\" Calibre 80"),
        ("MAT-003", "Cinta Embalaje Canela 48mm"),
        ("MAT-004", "Caja Corrugada Doble Corrugado L"),
        ("MAT-005", "Etiqueta Térmica 4x6"),
        ("MAT-006", "Sensor de Proximidad Industrial"),
        ("MAT-007", "Cable Industrial Blindado"),
        ("MAT-008", "Conector M12 Hembra 4-pines"),
        ("MAT-009", "Lubricante Sintético Alta Temp"),
        ("MAT-010", "Filtro de Aire Hepa H13")
    ]

    for sku, name in items_def:
        prod_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{sku}")
        stmt = select(Product).filter_by(id=prod_id, company_id=company_id)
        if not (await session.execute(stmt)).scalars().first():
            session.add(Product(
                id=prod_id, sku=sku, name=name, company_id=company_id,
                product_type=ProductType.GOODS, status=ProductStatus.ACTIVE,
                version_id=1, is_active=True, created_by=SYSTEM_USER_ID
            ))
            await session.flush()
            session.add(ProductVersion(
                id=uuid.uuid4(), product_id=prod_id, version_number=1,
                um_id=uom_pz_id, version_status=VersionStatus.PUBLISHED,
                is_active=True, is_validated=True, company_id=company_id,
                version_id=1, created_by=SYSTEM_USER_ID
            ))
            logger.info(f"    ➕ Producto: {sku}")

async def main(company_id: uuid.UUID):
    async with async_session() as session:
        try:
            logger.info("🌱 Iniciando Seeding de Master Data Service")
            
            # Garantizar tablas
            async with async_session().bind.begin() as conn:
                from common.domain import MultiTenantBase
                await conn.run_sync(MultiTenantBase.metadata.create_all)
            
            await seed_uoms(session)
            await seed_demo_products(session, company_id)
            await session.commit()
            logger.info("✅ Seeding completado con éxito.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error en seeding: {e}")
            raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--company-id", default=str(CO_LOGISTICS_ID))
    args = parser.parse_args()
    asyncio.run(main(company_id=uuid.UUID(args.company_id)))
