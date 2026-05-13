# -*- coding: utf-8 -*-
"""
test_density_guard.py -- Stress Test: Laissez-Faire Density Guard (Phase 63/64)
================================================================================
Protocolo:
  A) Obtiene warehouse y concepto reales de inventory_db (post-sync)
  B) Sincroniza BIN-STRESS-01 en master_data_db como SSOT (capacidad 10)
  C) Envia 500 unidades a BIN-STRESS-01 -> espera 200/202 (Laissez-Faire)
  D) El Auditor Silencioso detecta sobrecupo en background -> validation_status = OVERFLOW_CONFIRMED

Prerequisito:
  python backend/scripts/sync_seeds.py --company-id <COMPANY_ID>
"""
import sys
import io
import asyncio
import uuid
import requests
import time
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Force UTF-8 output to avoid Windows cp1252 issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# --- Configuration ---
AUTH_URL   = "http://localhost:8001/api/v1/auth"
INV_URL    = "http://localhost:8006/api/v1"
INV_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/inventory_db"
MD_DB_URL  = "postgresql+asyncpg://user:password@localhost:5433/master_data_db"

USER_EMAIL = "charly@interno.com"
USER_PW    = "charly123"
COMPANY_ID = "ad6cc8a6-34f9-42df-8f29-28254e0ad242"
LOCATION   = "BIN-STRESS-01"


async def setup_test_environment():
    """
    Ensures structural data is ready in both MD and Inventory DBs.
    """
    wh_id, concept_id, product_id = None, None, None
    
    # 1. Fetch Basic IDs from Inventory (Assumes sync_seeds has run)
    inv_engine = create_async_engine(INV_DB_URL, pool_pre_ping=True)
    async with inv_engine.begin() as conn:
        rw = await conn.execute(text("""
            SELECT id FROM inventory_warehouses
            WHERE company_id = :cid AND is_transit = false
            LIMIT 1
        """), {"cid": COMPANY_ID})
        wh_id = rw.scalar()

        if not wh_id:
            print("[ERROR] No hay warehouses en inventory_db.")
            return None, None, None

        rc = await conn.execute(text("""
            SELECT id FROM inventory_movement_concepts
            WHERE company_id = :cid AND type = 'ENTRY' AND is_active = true
            LIMIT 1
        """), {"cid": COMPANY_ID})
        concept_id = rc.scalar()

        rp = await conn.execute(text("""
            SELECT product_id FROM inventory_item_variants
            WHERE company_id = :cid AND is_active = true
            LIMIT 1
        """), {"cid": COMPANY_ID})
        product_id = rp.scalar()
        if not product_id:
            product_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"item.{COMPANY_ID}.MAT-STRESS-01")

        # Local Shadow Guarantee
        await conn.execute(text("""
            INSERT INTO inventory_locations
                (id, company_id, tenant_id, warehouse_id, code, max_capacity, is_active, version_id)
            VALUES
                (:id, :cid, :cid, :wid, :loc, 10, true, 1)
            ON CONFLICT (company_id, warehouse_id, code) DO UPDATE SET
                max_capacity = 10, is_active = true
        """), {"id": uuid.uuid4(), "cid": COMPANY_ID, "wid": wh_id, "loc": LOCATION})
    await inv_engine.dispose()

    # 2. Master Data SSOT Guarantee (Important for background audit)
    md_engine = create_async_engine(MD_DB_URL, pool_pre_ping=True)
    async with md_engine.begin() as conn:
        await conn.execute(text("""
            INSERT INTO inventory_locations
                (id, company_id, tenant_id, warehouse_id, code, max_capacity, is_active, version_id)
            VALUES
                (:id, :cid, :cid, :wid, :loc, 10, true, 1)
            ON CONFLICT (company_id, warehouse_id, code) DO UPDATE SET
                max_capacity = 10, is_active = true
        """), {"id": uuid.uuid4(), "cid": COMPANY_ID, "wid": wh_id, "loc": LOCATION})
    await md_engine.dispose()

    print(f"[*] {LOCATION} sincronizada (Cap: 10) en MD e Inventory DB.")
    return wh_id, concept_id, product_id


def get_auth_token():
    print(f"[*] Autenticando {USER_EMAIL}...")
    r = requests.post(f"{AUTH_URL}/login", json={"email": USER_EMAIL, "password": USER_PW})
    selection_token = r.json().get("data", {}).get("selection_token")
    r2 = requests.post(
        f"{AUTH_URL}/select-company",
        json={"company_id": COMPANY_ID},
        headers={"X-Selection-Token": selection_token}
    )
    return r2.json().get("data", {}).get("access_token")


async def verify_silent_auditor(movement_id):
    """Wait and check if status became OVERFLOW_CONFIRMED."""
    print("[*] Esperando al Auditor Silencioso (3s)...")
    await asyncio.sleep(3)
    
    inv_engine = create_async_engine(INV_DB_URL, pool_pre_ping=True)
    async with inv_engine.begin() as conn:
        res = await conn.execute(text("""
            SELECT validation_status FROM inventory_movements WHERE id = :id
        """), {"id": movement_id})
        status = res.scalar()
        
    await inv_engine.dispose()
    return status


async def run_stress_test():
    print("\n" + "=" * 60)
    print("  DENSITY GUARD STRESS TEST -- Laissez-Faire (Phase 64)")
    print("=" * 60)

    wh_id, concept_id, product_id = await setup_test_environment()
    if not wh_id: return

    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "X-Company-ID": COMPANY_ID}

    correlation_id = str(uuid.uuid4())
    payload = {
        "warehouse_id": str(wh_id),
        "type": "IN",
        "concept_id": str(concept_id),
        "correlation_id": correlation_id,
        "items": [
            {
                "product_id": str(product_id),
                "sku": "MAT-STRESS-01",
                "quantity": 500,
                "uom_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "interno.uom.PZA")),
                "location": LOCATION,
                "unit_price": 10.0,
                "weight": 500.0,
            }
        ]
    }

    print(f"\n[*] INYECION: 500 uds -> {LOCATION} (cap=10)...")
    start = time.time()
    r = requests.post(f"{INV_URL}/inventory/documents", json=payload, headers=headers)
    end = time.time()

    if r.status_code in [200, 201, 202]:
        data = r.json()
        print(f"[OK] Status {r.status_code} en {((end-start)*1000):.1f}ms (Zero-Cost Confirmed)")
        
        # Get movement ID from response if available, or fetch from DB
        # For simplicity, we fetch the latest movement for this correlation
        inv_engine = create_async_engine(INV_DB_URL, pool_pre_ping=True)
        async with inv_engine.begin() as conn:
            res = await conn.execute(text("SELECT id FROM inventory_movements WHERE document_id = :id"), {"id": correlation_id})
            mov_id = res.scalar()
        await inv_engine.dispose()

        if mov_id:
            audit_status = await verify_silent_auditor(mov_id)
            print(f"[RESULT] Validation Status: {audit_status}")
            if audit_status == "OVERFLOW_CONFIRMED":
                print("\n[STRESS TEST PASSED] Auditor Silencioso detecto el sobrecupo correctamente.")
            else:
                print("\n[STRESS TEST INCOMPLETE] El Auditor no marco el sobrecupo. (Status: {audit_status})")
    else:
        print(f"[FAIL] Error {r.status_code}: {r.text}")

    print("=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
