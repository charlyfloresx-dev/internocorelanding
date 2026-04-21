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


async def resolve_flow_ids(session: AsyncSession) -> dict:
    """
    Retorna un dict con los IDs reales de la DB resueltos por codigo estable.
    Lanza RuntimeError si algún dato maestro no existe (indica que el seed no se ejecutó).
    """
    from master_app.models.warehouse import Warehouse
    from master_app.models.uom import UOM
    from master_app.models.product import Product
    from master_app.models.location import InventoryLocation

    # Almacen
    wh = (await session.execute(
        select(Warehouse).where(Warehouse.code == "WH-001", Warehouse.company_id == CO_ENTERPRISE_ID)
    )).scalars().first()
    if not wh:
        raise RuntimeError("Almacen WH-001 no encontrado. Ejecuta primero: python scripts/unified_industrial_seed.py")

    # UOM
    uom = (await session.execute(
        select(UOM).where(UOM.code == "PZ")
    )).scalars().first()
    if not uom:
        raise RuntimeError("UOM PZ no encontrada. Ejecuta primero: python scripts/unified_industrial_seed.py")

    # Producto
    prod = (await session.execute(
        select(Product).where(Product.sku == "ECM-600", Product.company_id == CO_ENTERPRISE_ID)
    )).scalars().first()
    if not prod:
        raise RuntimeError("Producto ECM-600 no encontrado. Ejecuta primero: python scripts/unified_industrial_seed.py")

    # Ubicacion
    loc = (await session.execute(
        select(InventoryLocation).where(InventoryLocation.code == "LOC-AUDIT-01")
    )).scalars().first()
    if not loc:
        raise RuntimeError("Ubicacion LOC-AUDIT-01 no encontrada. Ejecuta primero: python scripts/unified_industrial_seed.py")

    return {
        "company_id":   CO_ENTERPRISE_ID,
        "user_id":      USER_CHARLY_ID,
        "warehouse_id": wh.id,
        "uom_id":       uom.id,
        "product_id":   prod.id,
        "location_id":  loc.id,
        "location_code": loc.code,
        "location_capacity": float(loc.max_capacity),
    }
