"""
flow_3_internal_transfer.py
------------------------------
Flujo 3: Transferencia interna entre almacenes de la misma empresa.
Mueve 15 PZ de WH-001 a un almacen secundario WH-002.

Pre-requisito: flow_1_entry.py ejecutado (necesita stock en WH-001).
"""
import asyncio
import uuid
import sys
import os
import traceback
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, text

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from inventory_app.domain.entities.transfer_entities import InitiateTransferCommand, CompleteTransferCommand
from flows._shared_ids import resolve_flow_ids, CO_ENTERPRISE_ID, USER_CHARLY_ID

# Almacen secundario — ID estable derivado por nombre
WH_SECONDARY_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.WH-002-SECONDARY")


async def ensure_secondary_warehouse(session):
    now_tz = datetime.now(timezone.utc)
    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code,
            type, is_active, version_id, is_transit, created_at
        ) VALUES (
            :id, 'Almacen Secundario TJ', :co_id, :co_id, 'WH-002', 'MX',
            'PHYSICAL', TRUE, 1, FALSE, :now
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_SECONDARY_ID, "co_id": CO_ENTERPRISE_ID, "now": now_tz})


async def run_flow_3():
    print("=" * 50)
    print("FLUJO 3: TRANSFERENCIA INTERNA")
    print("Empresa: Interno Enterprise -> Interno Enterprise")
    print("=" * 50)

    try:
        async with AsyncSessionLocal() as session:
            ids = await resolve_flow_ids(session)
            await ensure_secondary_warehouse(session)
            await session.commit()

            repo = SQLAlchemyInventoryRepository(session)
            handler = TransferCommandHandler(session, repo)

            print("\n[SHIP] Iniciando envio interno (Despacho)...")
            cmd_init = InitiateTransferCommand(
                origin_company_id=ids["company_id"],
                destination_company_id=ids["company_id"],
                origin_warehouse_id=ids["warehouse_id"],
                destination_warehouse_id=WH_SECONDARY_ID,
                product_id=ids["product_id"],
                quantity=Decimal("15.0"),
                weight=Decimal("7.5"),
                uom_id=ids["uom_id"],
                initiated_by=ids["user_id"],
                transfer_price=None,
                customs_pedimento=None
            )

            transfer = await handler.initiate_transfer(cmd_init)
            await session.commit()
            print(f"OK  Despacho registrado. Estado: SHIPPED. Folio: {transfer.folio}")

            print("\n[RECV] Efectuando recepcion interna (Receive)...")
            cmd_complete = CompleteTransferCommand(
                transfer_id=transfer.id,
                received_by=ids["user_id"],
                receiver_company_id=ids["company_id"],
                received_quantity=Decimal("15.0")
            )

            await handler.complete_transfer(cmd_complete)
            await session.commit()
            print("OK  Recepcion exitosa. Transferencia COMPLETADA.")
            print(f"    Transfer ID : {transfer.id}")
            print(f"    Origen      : WH-001")
            print(f"    Destino     : WH-002 (Secundario)")

    except RuntimeError as e:
        print(f"\nERROR: {e}")
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_flow_3())
