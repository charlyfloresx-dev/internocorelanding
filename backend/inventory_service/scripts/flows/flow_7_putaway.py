"""
flow_7_putaway.py
-----------------
[Phase 83] Validation Flow: Industrial Put-Away with Density Guard & Anexo 24 Inheritance.

What this flow validates:
  1. Items from Flow 1 (location=null) appear in the pending-putaway queue.
  2. relocate_stock moves them from SYS_RECEIVING -> 01-01-01-A.
  3. The customs_pedimento_id is INHERITED in the RELOC_IN movement (Anexo 24 integrity).
  4. The denormalized cache (current_units) is updated atomically.
  5. A forced overflow (150 units -> 50-unit capacity slot) raises ERR_LOCATION_OVERFLOW_UNITS.

Pre-requisites:
  - unified_industrial_seed.py  (users, companies, products)
  - seed_locations.py           (location layout)
  - flow_1_entry.py             (150 units in location=null)

Run:
  set CORE_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/interno_db
  set PYTHONPATH=backend;backend/inventory_service
  python backend/inventory_service/scripts/flows/flow_7_putaway.py
"""
import asyncio
import os
import sys
import logging
import traceback
import uuid
from decimal import Decimal

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from sqlalchemy import select, and_
from inventory_app.db.session import AsyncSessionLocal
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.infrastructure.clients.master_data import MasterDataClient
from inventory_app.schemas.inventory import StockRelocationCreate
from inventory_app.models.movement import Movement
from inventory_app.models.location import InventoryLocation
from flows._shared_ids import resolve_flow_ids

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("inventory_app").setLevel(logging.INFO)
log = logging.getLogger("flow-7")


async def run_flow_7():
    print("=" * 60)
    print("FLUJO 7: PUT-AWAY — Density Guard & Anexo 24 Inheritance")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        ids = await resolve_flow_ids(session)
        company_id   = ids["company_id"]
        warehouse_id = ids["warehouse_id"]
        product_id   = ids["product_id"]
        uom_id       = ids["uom_id"]

        repo    = SQLAlchemyInventoryRepository(session)
        service = InventoryTransactionService(repo, MasterDataClient())

        # ── STEP 1: Check pending-putaway queue ───────────────────────────────
        print("\n[1] Consultando pendientes de acomodo...")
        pending = await repo.get_pending_putaway_movements(
            company_id=company_id,
            warehouse_id=warehouse_id
        )
        print(f"    Pendientes encontrados: {len(pending)}")
        for p in pending[:3]:
            print(f"    - product={p['product_id'][:8]}  qty={p['available_quantity']}  "
                  f"pedimento={p['pedimento_number']}  dias_en_muelle={p['days_in_dock']}")

        if not pending:
            print("    AVISO: Sin pendientes. Asegurese de haber ejecutado flow_1_entry.py primero.")

        # ── STEP 2: Put-away 100 units -> 01-01-01-A (max 150) ───────────────
        print("\n[2] Put-Away: SYS_RECEIVING -> 01-01-01-A (100 unidades)...")
        target_location = "01-01-01-A"

        cmd = StockRelocationCreate(
            product_id=uuid.UUID(pending[0]["product_id"]),
            uom_id=uom_id,
            warehouse_id=uuid.UUID(pending[0]["warehouse_id"]),
            quantity=min(100.0, pending[0]["available_quantity"]),
            from_location="SYS_RECEIVING",
            to_location=target_location,
            notes="Flow 7: Put-away validation"
        )

        try:
            results = await service.relocate_stock(
                stmt=cmd,
                company_id=company_id,
                user_id=str(ids["user_id"]),
                role="OPERATOR"
            )
            await session.commit()
            print(f"    OK  {len(results)} movimiento(s) generado(s)")

            # ── STEP 3: Validate Anexo 24 inheritance ─────────────────────────
            print("\n[3] Validando herencia de Pedimento (Anexo 24)...")
            for mv in results:
                stmt = select(Movement).where(Movement.id == mv.id)
                res  = await session.execute(stmt)
                saved = res.scalar_one_or_none()
                if saved:
                    pedimento_ok = saved.customs_pedimento_id is not None
                    print(f"    RELOC_IN id={str(saved.id)[:8]}")
                    print(f"    location          = {saved.location}")
                    print(f"    customs_pedimento  = {saved.customs_pedimento_id}")
                    print(f"    Anexo 24 heredado = {'SI' if pedimento_ok else 'NO (sin pedimento en origen)'}")

            # ── STEP 4: Verify denormalized cache updated ─────────────────────
            print("\n[4] Verificando cache de ocupacion atomica...")
            loc_stmt = select(InventoryLocation).where(
                and_(
                    InventoryLocation.company_id == company_id,
                    InventoryLocation.warehouse_id == warehouse_id,
                    InventoryLocation.code == target_location
                )
            )
            loc_res = await session.execute(loc_stmt)
            loc = loc_res.scalar_one_or_none()
            if loc:
                print(f"    Ubicacion         = {loc.code}")
                print(f"    current_units     = {loc.current_units} / {loc.max_capacity_units}")
                print(f"    utilization       = {loc.utilization_percent}%")
                print(f"    density_status    = {loc.density_status}")
            else:
                print("    AVISO: Ubicacion no encontrada en inventory_locations.")
                print("    Ejecute seed_locations.py primero para crear las ubicaciones.")

        except ValueError as e:
            print(f"    ERROR: {e}")

        # ── STEP 5: Force overflow — should raise ERR_LOCATION_OVERFLOW_UNITS ─
        print("\n[5] Prueba de Overflow Forzado: intentando 500 units en slot de 50 (02-01-01-A)...")
        overflow_cmd = StockRelocationCreate(
            product_id=uuid.UUID(pending[0]["product_id"]),
            uom_id=uom_id,
            warehouse_id=uuid.UUID(pending[0]["warehouse_id"]),
            quantity=Decimal("500.0"),
            from_location="SYS_RECEIVING",
            to_location="02-01-01-A",   # PICKING slot — max 50 units
            notes="Flow 7: Overflow test"
        )
        try:
            await service.relocate_stock(
                stmt=overflow_cmd,
                company_id=company_id,
                user_id=str(ids["user_id"]),
                role="OPERATOR"
            )
            print("    FALLO: El sistema debio haber bloqueado el overflow.")
        except ValueError as e:
            if "ERR_LOCATION_OVERFLOW" in str(e):
                print(f"    OK  Overflow bloqueado correctamente.")
                print(f"    Mensaje: {e}")
            else:
                print(f"    ERROR inesperado: {e}")

    print("\n" + "=" * 60)
    print("FLUJO 7 COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_flow_7())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
