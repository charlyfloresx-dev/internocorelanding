"""
flows/_shared_ids.py
---------------------
Resuelve dinámicamente los IDs de la base de datos del monolito
usando los CODIGOs estables del seed unificado (unified_industrial_seed.py).

IDs FIJOS (definidos en el seed como constantes):
  - CO_ENTERPRISE_ID -> 9cd9986b-89da-48b7-8733-26a2a1225b01
  - USER_CHARLY_ID   -> 69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38

IDs DINAMICOS (creados con uuid4, se resuelven por codigo):
  - Almacen   -> codigo "WH-001"
  - UOM       -> codigo "PZ"
  - Producto  -> sku    "SKU-PROD-01"
  - Ubicacion -> codigo "LOC-AUDIT-01"
"""
import uuid
import sys
import os

# Path setup — funciona tanto desde el host como desde el contenedor
_FLOWS_DIR   = os.path.dirname(os.path.abspath(__file__))   # .../scripts/flows
_SCRIPTS_DIR = os.path.dirname(_FLOWS_DIR)                   # .../scripts
_SERVICE_DIR = os.path.dirname(_SCRIPTS_DIR)                 # .../inventory_service
_BACKEND     = os.path.dirname(_SERVICE_DIR)                 # .../backend

for _p in [_BACKEND, _SERVICE_DIR, _SCRIPTS_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# --- IDs Fijos (SSOT: unified_industrial_seed.py) ---
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
USER_CHARLY_ID   = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
USER_RECEIVER_ID = uuid.uuid4()  # Usuario simulado para evitar ERR_SELF_RECEIPT_NOT_ALLOWED



async def resolve_flow_ids(session: AsyncSession) -> dict:
    """
    Retorna un dict con los IDs reales de la DB resueltos por codigo estable.
    Lanza RuntimeError si algún dato maestro no existe (indica que el seed no se ejecutó).
    """
    # from master_app.models.warehouse import Warehouse (Removed cross-service import)
    # from master_app.models.uom import UOM (Removed cross-service import)
    # from master_app.models.product import Product (Removed cross-service import)
    # from master_app.models.location import InventoryLocation (Removed cross-service import)
    from sqlalchemy import text
    from inventory_app.models.customs_pedimento import CustomsPedimento

    # Almacen
    # Almacen via Raw SQL (Querying inventory_warehouses shadow table in inventory_db)
    wh_res = await session.execute(
        text("SELECT id FROM inventory_warehouses WHERE code = 'WH-001' AND company_id = :cid"),
        {"cid": CO_ENTERPRISE_ID}
    )
    wh_id = wh_res.scalar()
    if not wh_id:
        raise RuntimeError("Almacen WH-001 no encontrado en inventory_warehouses. Ejecuta primero: python scripts/unified_industrial_seed.py")

    # UOM
    # UOM PZ uses a stable deterministic UUID from unified_industrial_seed.py
    uom_id = uuid.UUID("9e222ea8-d40b-427c-b91a-e839c4576dde")

    # Producto
    # Producto ECM-600 uses a stable deterministic UUID from PRODUCT_DATA
    prod_id = uuid.UUID("e0e0e0e0-e0e0-40e0-a0e0-000000000001")

    # Ubicacion
    # Ubicacion via Raw SQL
    loc_res = await session.execute(
        text("SELECT id, code, max_capacity_units FROM inventory_locations WHERE code = 'LOC-AUDIT-01'")
    )
    loc_row = loc_res.fetchone()
    if not loc_row:
        raise RuntimeError("Ubicacion LOC-AUDIT-01 no encontrada. Ejecuta primero: python scripts/unified_industrial_seed.py")
    
    loc_id, loc_code, loc_capacity = loc_row

    # Pedimento (Resolve any valid pedimento for the company)
    ped = (await session.execute(
        select(CustomsPedimento).where(CustomsPedimento.company_id == CO_ENTERPRISE_ID).limit(1)
    )).scalars().first()
    if not ped:
        raise RuntimeError("No se encontro Pedimento para Enterprise. Ejecuta primero: python backend/scripts/seed_customs.py")

    # Conceptos
    # Conceptos via Raw SQL (Querying inventory_movement_concepts shadow table in inventory_db)
    concepts_res = await session.execute(
        text("SELECT id, code FROM inventory_movement_concepts WHERE company_id = :cid"),
        {"cid": CO_ENTERPRISE_ID}
    )
    concepts = {row[1]: row[0] for row in concepts_res.fetchall()}

    return {
        "company_id":   CO_ENTERPRISE_ID,
        "user_id":      USER_CHARLY_ID,
        "receiver_id":  USER_RECEIVER_ID,
        "warehouse_id": wh_id,
        "uom_id":       uom_id,
        "product_id":   prod_id,
        "location_id":  loc_id,
        "location_code": loc_code,
        "location_capacity": float(loc_capacity),
        "pedimento_id": ped.id,
        "concepts":     concepts
    }
