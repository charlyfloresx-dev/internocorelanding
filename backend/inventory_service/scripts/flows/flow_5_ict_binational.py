"""
flow_5_ict_binational.py
--------------------------
Flujo 5: Transferencia binacional inter-company (MX -> US).
Logistics MX despacha a Logistics US con pedimento aduanal.

Nota: Requiere que flow_4 haya depositado stock en Logistics MX primero.
      Las companias MX/US y sus almacenes se aprovisionan al vuelo con IDs estables.
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
from flows._shared_ids import resolve_flow_ids, USER_CHARLY_ID

# IDs fijos del auth seed (auth_service/scripts/seed.py)
CO_LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
CO_LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")

# Almacenes con IDs estables por nombre
WH_LOGISTICS_MX_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.LOG-MX-TJ")
WH_LOGISTICS_US_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.LOG-US-SD")

PEDIMENTO = "244030001234567"


async def ensure_warehouses_and_pedimento(session):
    now = datetime.now(timezone.utc)

    for wh_id, name, code, country, co_id in [
        (WH_LOGISTICS_MX_ID, "Logistics MX TJ", "LOG-MX-TJ", "MX", CO_LOGISTICS_MX_ID),
        (WH_LOGISTICS_US_ID, "Logistics US SD", "LOG-US-SD", "US", CO_LOGISTICS_US_ID),
    ]:
        await session.execute(text("""
            INSERT INTO inventory_warehouses (
                id, name, company_id, tenant_id, code, country_code,
                type, is_active, version_id, is_transit, created_at
            ) VALUES (
                :id, :name, :co_id, :co_id, :code, :country,
                'PHYSICAL', TRUE, 1, FALSE, :now
            )
            ON CONFLICT (id) DO NOTHING;
        """), {"id": wh_id, "name": name, "co_id": co_id, "code": code, "country": country, "now": now})

    await session.execute(text("""
        INSERT INTO customs_pedimentos (
            id, pedimento_number, customs_key, customs_date, is_temporary,
            operation_type, is_active, version_id, created_at, company_id, tenant_id
        ) VALUES (
            :id, :ped, 'A1', :now_date, FALSE, 'IMPORT', TRUE, 1, :now, :co_mx, :co_mx
        )
        ON CONFLICT (pedimento_number) DO NOTHING;
    """), {"id": uuid.uuid4(), "ped": PEDIMENTO, "now": now, "now_date": now.date(), "co_mx": CO_LOGISTICS_MX_ID})


async def run_flow_5():
    print("=" * 55)
    print("FLUJO 5: TRANSFERENCIA BINACIONAL (INTER-COMPANY CROSS-BORDER)")
    print("Origen: Logistics MX (TJ) -> Destino: Logistics US (SD)")
    print("=" * 55)

    try:
        async with AsyncSessionLocal() as session:
            ids = await resolve_flow_ids(session)
            await ensure_warehouses_and_pedimento(session)
            await session.commit()

            repo = SQLAlchemyInventoryRepository(session)
            handler = TransferCommandHandler(session, repo)

            print("\n[EXPORT] Logistics MX despacha 5 PZ con pedimento al cruce...")
            cmd_init = InitiateTransferCommand(
                origin_company_id=CO_LOGISTICS_MX_ID,
                destination_company_id=CO_LOGISTICS_US_ID,
                origin_warehouse_id=WH_LOGISTICS_MX_ID,
                destination_warehouse_id=WH_LOGISTICS_US_ID,
                product_id=ids["product_id"],
                quantity=Decimal("5.0"),
                weight=Decimal("2.5"),
                uom_id=ids["uom_id"],
                initiated_by=USER_CHARLY_ID,
                concept_id=ids["concepts"].get("INT-TRA"),
                transfer_price=None,
                exchange_rate_dof=Decimal("20.1500"),
                risk_acknowledged=True,
                customs_pedimento=PEDIMENTO
            )

            transfer = await handler.initiate_transfer(cmd_init)
            await session.commit()
            print(f"OK  Cruce registrado. Folio: {transfer.folio}")
            print(f"    Pedimento   : {PEDIMENTO}")
            print(f"    Tipo cambio : $20.15 MXN/USD")

            print("\n[IMPORT] Aduana completada. Logistics US recibe el stock...")
            cmd_recv = CompleteTransferCommand(
                transfer_id=transfer.id,
                received_by=ids["receiver_id"],
                receiver_company_id=CO_LOGISTICS_US_ID,
                received_quantity=Decimal("5.0"),
                concept_id=ids["concepts"].get("INT-TRA")
            )

            await handler.complete_transfer(cmd_recv)
            await session.commit()
            print("OK  Inventario dado de alta en Logistics US. Transito cerrado.")
            print(f"    Transfer ID : {transfer.id}")

    except RuntimeError as e:
        print(f"\nERROR: {e}")
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_flow_5())
