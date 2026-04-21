import asyncio
import argparse
import uuid
import logging
import os
import sys
from datetime import datetime, timezone

# Ajuste de path para encontrar 'app' y 'common'
sys.path.append(os.getcwd())

from master_app.db.db import async_session
from master_app.models.uom import UOM
from master_app.models.product import Product, ProductVersion
from master_app.models.product_price import ProductPrice, UnitType
from master_app.models.movement_concept import MovementConcept
from master_app.models.warehouse import Warehouse
from master_app.models.product_category import ProductCategory
from master_app.models.partner import Partner
from common.enums import ProductStatus, VersionStatus, ProductType, MovementType, WarehouseType, PartnerType
from sqlalchemy import select, delete

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("seed_master_data")

# --- CONSTANTES ---
CO_LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
CO_LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")
INTERNO_CORP_ID  = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01") # Interno Enterprise
SYSTEM_USER_ID   = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38") # Unified with Auth Charly ID
# UOMs son catálogos globales: usamos un tenant_id/company_id de sistema
GLOBAL_SYSTEM_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

from common.models.company import Company

async def seed_companies(session):
    logger.info("  [MD] Cargando compañías base...")
    companies_to_seed = [
        {"id": INTERNO_CORP_ID, "name": "Interno Enterprise", "status": "ACTIVE"},
        {"id": CO_LOGISTICS_MX_ID, "name": "Interno Logistic MX", "status": "ACTIVE"},
        {"id": CO_LOGISTICS_US_ID, "name": "Interno Logistic US", "status": "ACTIVE"},
        {"id": GLOBAL_SYSTEM_ID, "name": "System Global Context", "status": "SYSTEM"},
    ]
    for co in companies_to_seed:
        existing = await session.get(Company, co["id"])
        if not existing:
            session.add(Company(
                id=co["id"], name=co["name"], status=co["status"],
                is_active=True, version_id=1, created_by=SYSTEM_USER_ID
            ))
            logger.info(f"    ➕ Compañía: {co['name']}")
    await session.flush()

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
                id=id_,
                company_id=GLOBAL_SYSTEM_ID,  # Catálogo global: usa ID de sistema
                tenant_id=GLOBAL_SYSTEM_ID,
                code=uom_data["code"],
                name=uom_data["name"], plural=uom_data["plural"],
                is_active=True, version_id=1, created_by=SYSTEM_USER_ID
            ))
            logger.info(f"    ➕ UOM: {uom_data['code']}")
    await session.flush()

async def seed_categories(session):
    logger.info("  [MD] Cargando Categorías globales...")
    categories_to_seed = [
        {"code": "RAW", "name": "Materias Primas"},
        {"code": "WIP", "name": "Trabajo en Proceso"},
        {"code": "FIN", "name": "Producto Terminado"},
        {"code": "MRO", "name": "Mantenimiento y Operación"}
    ]
    for cat in categories_to_seed:
        cat_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"cat.{cat['code']}")
        existing = await session.get(ProductCategory, cat_id)
        if not existing:
            session.add(ProductCategory(
                id=cat_id,
                company_id=GLOBAL_SYSTEM_ID,
                tenant_id=GLOBAL_SYSTEM_ID,
                code=cat["code"],
                name=cat["name"],
                is_active=True, version_id=1, created_by=SYSTEM_USER_ID
            ))
            logger.info(f"    ➕ Categoría: {cat['code']}")
    await session.flush()

async def seed_demo_products(session, company_id: uuid.UUID):
    logger.info(f"  [MD] Cargando catálogo demo para company: {company_id}")
    uom_pz_id = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")
    
    items_def = [
        ("MAT-001", "Aluminio Industrial 6061-T6", "72171101", "7604.21.0000"),
        ("MAT-002", "Película Stretch 20\" Especial", "31151606", "3920.10.0000"),
        ("MAT-003", "Ahesivo de Contacto Industrial", "31201610", "3506.10.0000"),
        ("MAT-004", "Empaque Corrugado Reforzado", "24112310", "4819.10.0000"),
        ("MAT-005", "Resina Epóxica Grado Pro", "31201525", "3907.30.0000"),
        ("MAT-006", "Sensor Capacitivo M18", "41111961", "8536.50.0000"),
        ("MAT-007", "Cable Blindado de Potencia", "26121603", "8544.49.0000"),
        ("MAT-008", "Rodamiento de Rodillos Timken", "31171505", "8482.20.0000"),
        ("MAT-009", "Lubricante Térmico Sintético", "15121502", "3403.99.0000"),
        ("MAT-010", "Filtro Hepa Alta Eficiencia", "40161505", "8421.39.0000")
    ]

    for i, (sku, name, sat, hts) in enumerate(items_def):
        prod_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{company_id}.{sku}")
        stmt = select(Product).filter_by(id=prod_id, company_id=company_id)
        existing = (await session.execute(stmt)).scalars().first()
        if not existing:
            session.add(Product(
                id=prod_id, sku=sku, name=name, company_id=company_id,
                tenant_id=company_id,
                sat_product_code=sat,
                hts_code=hts,
                is_taxable=True,
                allow_price_override=True,
                product_type=ProductType.GOODS, status=ProductStatus.ACTIVE,
                version_id=1, is_active=True, created_by=SYSTEM_USER_ID
            ))
            await session.flush()
            session.add(ProductVersion(
                id=uuid.uuid4(), product_id=prod_id, version_number=1,
                um_id=uom_pz_id, version_status=VersionStatus.PUBLISHED,
                is_active=True, is_validated=True, company_id=company_id,
                tenant_id=company_id,
                version_id=1, created_by=SYSTEM_USER_ID
            ))
            logger.info(f"    ➕ Producto: {sku}")
        else:
            existing.name = name
            logger.info(f"    🔄 Producto {sku} actualizado.")
            
        # Seed Prices for tiers 1-4 (only if not exists)
        # Using a deterministic logic for prices based on sku index and tier
        base_price = 100.0 + (i * 15.5)
        for tier in range(1, 5):
            discount = (tier - 1) * 0.15 # Tier 1: 0%, Tier 2: 15%, Tier 3: 30%, Tier 4: 45%
            amount = base_price * (1.0 - discount)
            
            stmt_price = select(ProductPrice).filter_by(
                product_id=prod_id, company_id=company_id, price_list_index=tier, _currency="USD", unit_type="BASE", warehouse_id=None, is_active=True
            )
            existing_price = (await session.execute(stmt_price)).scalars().first()
            if not existing_price:
                from _decimal import Decimal
                session.add(ProductPrice(
                    id=uuid.uuid4(),
                    product_id=prod_id,
                    company_id=company_id,
                    tenant_id=company_id,
                    price_list_index=tier,
                    _amount=Decimal(str(round(amount, 2))),
                    _currency="USD",
                    unit_type=UnitType.SALE,
                    warehouse_id=None,
                    is_active=True,
                    version_id=1,
                    created_by=SYSTEM_USER_ID
                ))
                logger.info(f"      💵 Precio Tier {tier} añadido.")
        await session.flush()

async def seed_concepts_and_warehouses(session, company_id: uuid.UUID, country: str = "MX"):
    # 1. Conceptos (upsert)
    concepts = [
        {"code": "ENT-PUR", "name": "Compra",           "type": MovementType.ENTRY, "requires_external_entity": True},
        {"code": "ENT-ADJ", "name": "Ajuste Positivo",   "type": MovementType.ENTRY},
        {"code": "SAL-VEN", "name": "Venta",             "type": MovementType.OUTPUT, "requires_external_entity": True},
        {"code": "SAL-ADJ", "name": "Ajuste Negativo",   "type": MovementType.OUTPUT},
        {"code": "TRF-INT", "name": "Traspaso Interno",  "type": MovementType.TRANSFER,
         "requires_target_warehouse": True},
    ]

    for c_data in concepts:
        c_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.concept.{company_id}.{c_data['code']}")
        stmt = select(MovementConcept).filter_by(id=c_id, company_id=company_id)
        existing = (await session.execute(stmt)).scalars().first()
        if not existing:
            session.add(MovementConcept(
                id=c_id,
                company_id=company_id,
                tenant_id=company_id,
                code=c_data["code"],
                name=c_data["name"],
                type=c_data["type"],
                requires_external_entity=c_data.get("requires_external_entity", False),
                requires_target_warehouse=c_data.get("requires_target_warehouse", False),
                is_active=True,
                created_by=SYSTEM_USER_ID,
                version_id=1
            ))
            logger.info(f"    ➕ Concepto: {c_data['code']}")
    await session.flush()
    
    # 2. Almacenes — PURGE first to eliminate ghost records, then insert clean
    logger.info(f"  [MD] Purgando almacenes anteriores para company: {company_id}")
    await session.execute(delete(Warehouse).where(Warehouse.company_id == company_id))
    await session.flush()
    
    if country == "MX":
        warehouses = [
            {"code": "WH-TIJ", "name": "Tijuana Central",       "type": WarehouseType.PHYSICAL,  "country": "MX"},
            {"code": "WH-QUARANTINE", "name": "Cuarentena / Calidad", "type": WarehouseType.VIRTUAL, "country": "MX"},
            {"code": "WH-ENS", "name": "Ensenada Port",          "type": WarehouseType.PHYSICAL,  "country": "MX"},
        ]
    else:
        warehouses = [
            {"code": "WH-SDY", "name": "San Diego Hub", "type": WarehouseType.TRANSIT,  "country": "US"},
            {"code": "WH-OTY", "name": "Otay Mesa",     "type": WarehouseType.PHYSICAL, "country": "US"},
        ]

    for w_data in warehouses:
        w_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_id}.{w_data['code']}")
        session.add(Warehouse(
            id=w_id,
            company_id=company_id,
            tenant_id=company_id,
            code=w_data["code"],
            name=w_data["name"],
            type=w_data["type"],
            country_code=w_data["country"],
            is_active=True,
            is_production_resource=w_data.get("is_resource", False),
            created_by=SYSTEM_USER_ID,
            version_id=1
        ))
        logger.info(f"    ➕ Almacén: {w_data['code']} [{w_data['country']}]")
    await session.flush()

async def seed_partners(session, company_id: uuid.UUID):
    logger.info(f"  [MD] Cargando Partners para company: {company_id}")
    partners_to_seed = [
        {"code": "SUP-GLO", "name": "Supplier Global Solutions", "type": PartnerType.SUPPLIER, "tax_id": "RFC-SUP-001"},
        {"code": "SUP-LOC", "name": "Local Industrial Supplies", "type": PartnerType.SUPPLIER, "tax_id": "RFC-SUP-002"},
        {"code": "CUS-INT", "name": "Internal Corp Client", "type": PartnerType.CUSTOMER, "tax_id": "RFC-CUS-001"},
        {"code": "CUS-EXT", "name": "External Logistics Partner", "type": PartnerType.BOTH, "tax_id": "RFC-CUS-002"},
    ]
    for p_data in partners_to_seed:
        p_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.partner.{company_id}.{p_data['code']}")
        existing = await session.get(Partner, p_id)
        if not existing:
            session.add(Partner(
                id=p_id,
                company_id=company_id,
                tenant_id=company_id,
                code=p_data["code"],
                name=p_data["name"],
                type=p_data["type"],
                tax_id=p_data["tax_id"],
                is_active=True,
                created_by=SYSTEM_USER_ID,
                version_id=1
            ))
            logger.info(f"    ➕ Partner: {p_data['code']}")
    await session.flush()

async def main():
    async with async_session() as session:
        try:
            logger.info("🌱 Iniciando Seeding de Master Data Service (MULTITENANT)")

            await seed_companies(session)
            await seed_uoms(session)
            await seed_categories(session)
            
            # SEED MX Entity
            await seed_demo_products(session, CO_LOGISTICS_MX_ID)
            await seed_concepts_and_warehouses(session, CO_LOGISTICS_MX_ID, country="MX")
            await seed_product_prices(session, CO_LOGISTICS_MX_ID)
            await seed_partners(session, CO_LOGISTICS_MX_ID)
            
            # SEED US Entity
            await seed_demo_products(session, CO_LOGISTICS_US_ID)
            await seed_concepts_and_warehouses(session, CO_LOGISTICS_US_ID, country="US")
            await seed_product_prices(session, CO_LOGISTICS_US_ID)
            await seed_partners(session, CO_LOGISTICS_US_ID)

            # SEED InternoCorp Enterprise (New National Entity)
            await seed_demo_products(session, INTERNO_CORP_ID)
            await seed_concepts_and_warehouses(session, INTERNO_CORP_ID, country="MX")
            await seed_product_prices(session, INTERNO_CORP_ID)
            await seed_partners(session, INTERNO_CORP_ID)

            await session.commit()
            logger.info("✅ Seeding multitenant completado con éxito.")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error en seeding: {e}")
            import traceback
            traceback.print_exc()
            raise

async def seed_product_prices(session, company_id: uuid.UUID):
    logger.info(f"  [MD] Cargando Listas de Precios para company: {company_id}")
    from decimal import Decimal
    
    # Precios globales para MAT-001 y MAT-002
    prices_def = [
        # (SKU, ListIndex, Amount, Currency, UnitType, WarehouseKey)
        ("MAT-001", 1, 150.00, "USD", "BASE", None),
        ("MAT-002", 1, 25.50, "USD", "BASE", None),
        # Precio especial en Tijuana Central
        ("MAT-001", 1, 145.00, "USD", "BASE", "WH-TIJ"),
        # Precio especial en San Diego Hub (USD)
        ("MAT-002", 1, 24.00, "USD", "BASE", "WH-SDY"),
    ]

    for sku, idx, amt, curr, utype, wh_key in prices_def:
        prod_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.item.{company_id}.{sku}")
        wh_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"interno.warehouse.{company_id}.{wh_key}") if wh_key else None
        
        stmt = select(ProductPrice).filter_by(
            company_id=company_id,
            product_id=prod_id,
            price_list_index=idx,
            unit_type=utype,
            warehouse_id=wh_id,
            _currency=curr,
            is_active=True
        )
        existing = (await session.execute(stmt)).scalars().first()
        
        if not existing:
            session.add(ProductPrice(
                id=uuid.uuid4(),
                company_id=company_id,
                tenant_id=company_id,
                product_id=prod_id,
                price_list_index=idx,
                _amount=Decimal(str(amt)),
                _currency=curr,
                unit_type=UnitType.SALE,
                warehouse_id=wh_id,
                is_active=True,
                version_id=1,
                created_by=SYSTEM_USER_ID
            ))
            logger.info(f"    ➕ Precio {idx} para {sku} ({wh_key or 'GLOBAL'})")
    
    await session.flush()

if __name__ == "__main__":
    asyncio.run(main())
