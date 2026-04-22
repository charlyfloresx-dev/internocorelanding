"""
flow_4_ict_enterprise_to_logistics.py
-----------------------------------------
Flujo 4: Transferencia inter-company nacional.
Origen: Interno Enterprise (WH-001, MX) -> Destino: Interno Logistics MX.

Nota: Este flow usa la empresa Enterprise como origen (SSOT del seed).
El destino (Logistics MX) se aprovisiona al vuelo con IDs estables.

Pre-requisito: flow_1_entry.py ejecutado.
"""
import asyncio
import uuid
import sys
import os
import traceback
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import text

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from inventory_app.domain.entities.transfer_entities import InitiateTransferCommand, CompleteTransferCommand
from flows._shared_ids import resolve_flow_ids, CO_ENTERPRISE_ID, USER_CHARLY_ID

# IDs fijos del auth seed (seed.py del auth_service)
CO_LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")

# Almacen destino — ID estable por nombre
WH_LOGISTICS_MX_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.LOG-MX-TJ")


async def ensure_logistics_warehouse(session):
    now = datetime.now(timezone.utc)
    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code,
            type, is_active, version_id, is_transit, created_at
        ) VALUES (
            :id, 'Logistics MX TJ', :co_id, :co_id, 'LOG-MX-TJ', 'MX',
            'PHYSICAL', TRUE, 1, FALSE, :now
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_LOGISTICS_MX_ID, "co_id": CO_LOGISTICS_MX_ID, "now": now})


async def run_flow_4():
    print("=" * 55)
    print("FLUJO 4: TRANSFERENCIA INTER-COMPANY (NACIONAL)")
    print("Origen: Interno Enterprise -> Destino: Interno Logistics MX")
    print("=" * 55)

    try:
        async with AsyncSessionLocal() as session:
            ids = await resolve_flow_ids(session)
            await ensure_logistics_warehouse(session)
            await session.commit()

            repo = SQLAlchemyInventoryRepository(session)
            handler = TransferCommandHandler(session, repo)

            print("\n[SHIP] Enterprise despacha 25 PZ a Logistics MX...")
            cmd_init = InitiateTransferCommand(
                origin_company_id=ids["company_id"],
                destination_company_id=CO_LOGISTICS_MX_ID,
                origin_warehouse_id=ids["warehouse_id"],
                destination_warehouse_id=WH_LOGISTICS_MX_ID,
                product_id=ids["product_id"],
                quantity=Decimal("25.0"),
                weight=Decimal("12.5"),
                uom_id=ids["uom_id"],
                initiated_by=ids["user_id"],
                concept_id=ids["concepts"].get("INT-TRA"),
                transfer_price=Decimal("15.75"),
                customs_pedimento=None
            )

            transfer = await handler.initiate_transfer(cmd_init)
            await session.commit()
            print(f"OK  Transferencia en transito. Folio ICT: {transfer.folio}")

            print("\n[RECV] Logistics MX recibe el stock...")
            cmd_recv = CompleteTransferCommand(
                transfer_id=transfer.id,
                received_by=ids["receiver_id"],
                receiver_company_id=CO_LOGISTICS_MX_ID,
                received_quantity=Decimal("25.0"),
                concept_id=ids["concepts"].get("INT-TRA")
            )

            await handler.complete_transfer(cmd_recv)
            await session.commit()
            print("OK  Recepcion validada. Stock disponible en Logistics MX.")
            print(f"    Transfer ID : {transfer.id}")
            print(f"    Precio ICT  : $15.75 MXN/PZ")

    except RuntimeError as e:
        print(f"\nERROR: {e}")
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_flow_4())
