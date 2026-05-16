import asyncio
import os
import sys
import logging
import uuid
from decimal import Decimal

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.infrastructure.clients.master_data import MasterDataClient
from inventory_app.schemas.inventory import StockRelocationCreate
from flows._shared_ids import resolve_flow_ids

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("flow-relocation")

async def run_flow_relocation():
    print("=" * 60)
    print("FLUJO: REUBICACION ATOMICA (Phase 83)")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyInventoryRepository(session)
        md_client = MasterDataClient()
        service = InventoryTransactionService(repo, md_client)
        
        ids = await resolve_flow_ids(session)
        co_id = ids["company_id"]
        
        # 1. RACK TO RACK RELOCATION
        # Source: LOC-AUDIT-01 (should have stock from entry/adjustments)
        # Target: 01-01-01-A
        print("\n[1] Ejecutando Reubicación: LOC-AUDIT-01 -> 01-01-01-A (10 unidades)...")
        reloc_cmd = StockRelocationCreate(
            product_id=ids["product_id"],
            warehouse_id=ids["warehouse_id"],
            from_location="LOC-AUDIT-01",
            to_location="01-01-01-A",
            quantity=Decimal("10.0"),
            uom_id=ids["uom_id"],
            correlation_id=uuid.uuid4()
        )
        
        results = await service.relocate_stock(
            stmt=reloc_cmd,
            company_id=co_id,
            user_id=str(ids["user_id"])
        )
        await session.commit()
        print(f"    OK: {len(results)} movimientos generados.")

        # 2. VERIFY OCCUPANCY
        print("\n[2] Verificando Ocupación de Destino (01-01-01-A)...")
        loc = await repo.get_location_entity(ids["warehouse_id"], "01-01-01-A", co_id)
        if loc:
            print(f"    Ocupación Actual: {loc.current_units} / {loc.max_capacity_units}")
            print(f"    Estatus Densidad: {loc.density_status}")

    print("\n" + "=" * 60)
    print("FLUJO DE REUBICACION COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_flow_relocation())
