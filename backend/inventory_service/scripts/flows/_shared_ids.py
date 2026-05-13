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
    # Almacen via Raw SQL
    wh_res = await session.execute(
        text("SELECT id FROM warehouses WHERE code = 'WH-001' AND company_id = :cid"),
        {"cid": CO_ENTERPRISE_ID}
    )
    wh_id = wh_res.scalar()
    if not wh_id:
        raise RuntimeError("Almacen WH-001 no encontrado. Ejecuta primero: python scripts/unified_industrial_seed.py")

    # UOM
    # UOM via Raw SQL
    uom_res = await session.execute(
        text("SELECT id FROM uoms WHERE code = 'PZ'")
    )
    uom_id = uom_res.scalar()
    if not uom_id:
        raise RuntimeError("UOM PZ no encontrada. Ejecuta primero: python scripts/unified_industrial_seed.py")

    # Producto
    # Producto via Raw SQL
    prod_res = await session.execute(
        text("SELECT id FROM products WHERE sku = 'ECM-600' AND company_id = :cid"),
        {"cid": CO_ENTERPRISE_ID}
    )
    prod_id = prod_res.scalar()
    if not prod_id:
        raise RuntimeError("Producto ECM-600 no encontrado. Ejecuta primero: python scripts/unified_industrial_seed.py")

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
    # Conceptos via Raw SQL
    # from master_app.models.movement_concept import MovementConcept (Removed cross-service import)
    concepts_res = await session.execute(
        text("SELECT id, code FROM movement_concepts WHERE group_id = :gid"),
        {"gid": uuid.UUID("eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e")}
    )
    concepts = {row[1]: row[0] for row in concepts_res.fetchall()}
    
    # Fallback to local codes if group inheritance not found in DB yet
    if not concepts:
        concepts_res = await session.execute(
            text("SELECT id, code FROM movement_concepts WHERE company_id = :cid"),
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
