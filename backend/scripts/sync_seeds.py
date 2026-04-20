"""
sync_seeds.py — Cross-Service Seed Alignment Script
=====================================================
Propósito:
    Sincroniza las entidades estructurales de master_data_db hacia inventory_db
    para garantizar consistencia entre microservicios.

Qué hace:
    1. Copia inventory_warehouses desde master_data_db → inventory_db
    2. Crea MovementConcepts básicos en inventory_db si no existen
    3. Siembra inventory_locations en inventory_db (SSOT local del density guard)

Uso:
    python backend/scripts/sync_seeds.py --company-id <UUID>
    python backend/scripts/sync_seeds.py --company-id <UUID> --add-stress-location
"""

import asyncio
import uuid
import logging
import argparse
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("sync_seeds")

# ─── DB URLs ──────────────────────────────────────────────────────────────────
MASTER_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"
INVENTORY_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/inventory_db"

# Warehouses query ignores transit (no is_transit column in master_data_db.warehouses)
WAREHOUSE_QUERY = """
    SELECT id, company_id, tenant_id, group_id, code, name, description,
           type, country_code, is_active, created_at, created_by, version_id
    FROM warehouses
    WHERE company_id = :company_id
"""

CONCEPT_DEFAULTS = [
    {"code": "ENT-COMPRA", "name": "Entrada por Compra",    "type": "ENTRY",      "affects_stock": True},
    {"code": "ENT-ADJ",    "name": "Ajuste de Entrada",     "type": "ENTRY",      "affects_stock": True},
    {"code": "SAL-VENTA",  "name": "Salida por Venta",      "type": "OUTPUT",     "affects_stock": True},
    {"code": "SAL-ADJ",    "name": "Ajuste de Salida",      "type": "OUTPUT",     "affects_stock": True},
    {"code": "TRANS",      "name": "Transferencia Interna", "type": "TRANSFER",   "affects_stock": True},
]


async def sync_warehouses(company_id: uuid.UUID, master_conn, inv_conn):
    logger.info(f"[1/3] Sincronizando inventory_warehouses para company={company_id}")

    rows = (await master_conn.execute(text(WAREHOUSE_QUERY), {"company_id": str(company_id)})).fetchall()
    if not rows:
        logger.warning("  ⚠️  No se encontraron warehouses en master_data_db para esa empresa.")
        return []

    synced_ids = []
    for row in rows:
        wh_id = row[0]
        wh_company_id = row[1]
        wh_tenant_id = row[2]
        wh_group_id = row[3]
        wh_code = row[4]
        wh_name = row[5]
        wh_description = row[6]
        wh_type = row[7]
        wh_country_code = row[8]
        wh_is_active = row[9]
        wh_created_at = row[10]
        wh_created_by = row[11]
        wh_version_id = row[12]

        await inv_conn.execute(text("""
            INSERT INTO inventory_warehouses
                (id, company_id, tenant_id, group_id, code, name, description,
                 type, country_code, is_active, location, is_transit,
                 created_at, created_by, version_id)
            VALUES
                (:id, :company_id, :tenant_id, :group_id, :code, :name, :description,
                 :type, :country_code, :is_active, NULL, false,
                 :created_at, :created_by, :version_id)
            ON CONFLICT (id) DO UPDATE SET
                name       = EXCLUDED.name,
                is_active  = EXCLUDED.is_active
        """), {
            "id": wh_id,
            "company_id": wh_company_id,
            "tenant_id": wh_tenant_id or wh_company_id,
            "group_id": wh_group_id,
            "code": wh_code,
            "name": wh_name,
            "description": wh_description,
            "type": wh_type,
            "country_code": wh_country_code,
            "is_active": wh_is_active,
            "created_at": wh_created_at,
            "created_by": wh_created_by,
            "version_id": wh_version_id or 1,
        })
        synced_ids.append(wh_id)
        logger.info(f"  ✅ Warehouse sincronizado: [{wh_code}] {wh_name} ({wh_id})")

    return synced_ids


async def seed_movement_concepts(company_id: uuid.UUID, inv_conn):
    logger.info(f"[2/3] Creando MovementConcepts en inventory_db para company={company_id}")

    existing = (await inv_conn.execute(
        text("SELECT code FROM inventory_movement_concepts WHERE company_id = :cid"),
        {"cid": str(company_id)}
    )).fetchall()
    existing_codes = {r[0] for r in existing}

    system_user = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

    for c in CONCEPT_DEFAULTS:
        if c["code"] in existing_codes:
            logger.info(f"  · Concepto ya existe: {c['code']}")
            continue

        concept_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"inventory.concept.{company_id}.{c['code']}")
        await inv_conn.execute(text("""
            INSERT INTO inventory_movement_concepts
                (id, company_id, tenant_id, code, name, type, affects_stock, currency, is_active, version_id, created_by)
            VALUES
                (:id, :company_id, :company_id, :code, :name, :type, :affects_stock, 'MXN', true, 1, :created_by)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": concept_id,
            "company_id": str(company_id),
            "code": c["code"],
            "name": c["name"],
            "type": c["type"],
            "affects_stock": c["affects_stock"],
            "created_by": str(system_user),
        })
        logger.info(f"  ✅ Concepto creado: {c['code']} ({concept_id})")


async def seed_stress_location(company_id: uuid.UUID, warehouse_ids: list, inv_conn):
    logger.info(f"[3/3] Sembrando BIN-STRESS-01 en inventory_db para Density Guard test")

    if not warehouse_ids:
        logger.warning("  ⚠️  No hay warehouses sincronizados. Saltando ubicación de stress.")
        return

    # Use the first physical warehouse
    wh_id = warehouse_ids[0]
    location_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"inventory.location.{company_id}.{wh_id}.BIN-STRESS-01")
    system_user = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

    await inv_conn.execute(text("""
        INSERT INTO inventory_locations
            (id, company_id, tenant_id, warehouse_id, code, max_capacity, is_active, version_id, created_by)
        VALUES
            (:id, :cid, :cid, :wid, 'BIN-STRESS-01', 10, true, 1, :created_by)
        ON CONFLICT (company_id, warehouse_id, code) DO UPDATE SET
            max_capacity = 10,
            is_active    = true
    """), {
        "id": location_id,
        "cid": str(company_id),
        "wid": wh_id,
        "created_by": str(system_user),
    })
    logger.info(f"  ✅ BIN-STRESS-01 sembrada en warehouse {wh_id} (cap=10)")


async def main():
    parser = argparse.ArgumentParser(description="InternoCore — Cross-Service Seed Alignment")
    parser.add_argument("--company-id", required=True, help="Company UUID to sync")
    parser.add_argument("--add-stress-location", action="store_true",
                        help="Also seed BIN-STRESS-01 for Density Guard testing")
    args = parser.parse_args()
    company_id = uuid.UUID(args.company_id)

    master_engine = create_async_engine(MASTER_DB_URL, echo=False)
    inv_engine = create_async_engine(INVENTORY_DB_URL, echo=False)

    try:
        async with master_engine.begin() as master_conn:
            async with inv_engine.begin() as inv_conn:
                synced_ids = await sync_warehouses(company_id, master_conn, inv_conn)
                await seed_movement_concepts(company_id, inv_conn)
                if args.add_stress_location:
                    await seed_stress_location(company_id, synced_ids, inv_conn)

        logger.info("\n🏁 Alineación de seeds completada exitosamente.")
    finally:
        await master_engine.dispose()
        await inv_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
