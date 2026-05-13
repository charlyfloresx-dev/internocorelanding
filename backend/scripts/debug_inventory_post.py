"""
debug_inventory_post.py
-----------------------
Simula el POST /api/v1/inventory/documents usando IDs REALES de la DB.
Todos los IDs se resuelven dinámicamente desde la base de datos para evitar
desincronización entre seeds y scripts de prueba.
"""
import requests
import json
import asyncio
import sys
import os
import uuid

# Setup paths for imports
_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

BASE_URL = "http://localhost:8000"

# ─── IDs fijos (SSOT: unified_industrial_seed.py) ───
COMPANY_ID = "9cd9986b-89da-48b7-8733-26a2a1225b01"


async def resolve_ids():
    """Resolve real IDs from DB to avoid hardcoded mismatches."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    db_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/dbname")
    engine = create_async_engine(db_url, pool_pre_ping=True)

    async with engine.connect() as conn:
        # Warehouse
        wh = await conn.execute(text(
            "SELECT id FROM inventory_warehouses WHERE code = 'WH-001' AND company_id = :co LIMIT 1"
        ), {"co": COMPANY_ID})
        warehouse_id = str(wh.scalar_one())

        # Concept (SAL-VEN for OUT)
        con = await conn.execute(text(
            "SELECT id FROM movement_concepts WHERE code = 'SAL-VEN' LIMIT 1"
        ))
        concept_id = str(con.scalar_one())

        # UOM (PZ)
        uom = await conn.execute(text(
            "SELECT id FROM uoms WHERE code = 'PZ' LIMIT 1"
        ))
        uom_id = str(uom.scalar_one())

        # Product
        product_id = "e0e0e0e0-e0e0-40e0-a0e0-000000000001"

    await engine.dispose()
    return {
        "warehouse_id": warehouse_id,
        "concept_id": concept_id,
        "uom_id": uom_id,
        "product_id": product_id,
    }


def debug_inventory_post(ids: dict):
    url = f"{BASE_URL}/api/v1/inventory/documents"

    trace_uuid = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Master-Key": "GOD_MODE_ACTIVE",
        "X-Company-ID": COMPANY_ID,
        "X-Trace-Id": trace_uuid,
        "X-Client-Request-ID": trace_uuid,
    }

    payload = {
        "correlation_id": trace_uuid,
        "type": "OUT",
        "concept_id": ids["concept_id"],
        "warehouse_id": ids["warehouse_id"],
        "notes": "Debug POST with real DB IDs",
        "items": [
            {
                "product_id": ids["product_id"],
                "sku": "ECM-600",
                "quantity": 1,
                "uom_id": ids["uom_id"],
                "weight": 0,
                "unit_price": 495,
                "location": None,
            }
        ],
    }

    print(f"[*] Resolved IDs from DB:")
    for k, v in ids.items():
        print(f"    {k}: {v}")
    print(f"\n[*] Sending POST to {url}...")

    response = requests.post(url, headers=headers, json=payload)
    print(f"[*] Status Code: {response.status_code}")
    try:
        print("[*] Response Body:")
        print(json.dumps(response.json(), indent=4))
    except Exception:
        print(f"[*] Raw Response: {response.text}")


if __name__ == "__main__":
    ids = asyncio.run(resolve_ids())
    debug_inventory_post(ids)
