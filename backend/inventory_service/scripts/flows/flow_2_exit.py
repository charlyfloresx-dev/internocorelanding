"""
flow_2_exit.py
----------------
Flujo 2: Salida de inventario (OUT).
Descarga 20 unidades del producto SKU-PROD-01 desde almacen WH-001.

Pre-requisito: flow_1_entry.py ejecutado primero (necesita stock disponible).
"""
import asyncio
import uuid
import sys
import os
import traceback
from decimal import Decimal
from datetime import datetime, timezone

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money
from inventory_app.models.document import InventoryDocument, DocumentStatus
from flows._shared_ids import resolve_flow_ids


async def run_flow_2():
    print("=" * 50)
    print("FLUJO 2: SALIDA DE INVENTARIO (OUT)")
    print("Empresa: Interno Enterprise")
    print("=" * 50)

    try:
        async with AsyncSessionLocal() as session:
            ids = await resolve_flow_ids(session)

            doc_id = uuid.uuid4()

            doc_header = InventoryDocument(
                id=doc_id,
                company_id=ids["company_id"],
                tenant_id=ids["company_id"],
                folio=f"OUT-{doc_id.hex[:6].upper()}",
                document_type="OUT",
                status=DocumentStatus.PROCESSED,
                origin_name="STOCK",
                destination_name="CLIENTE / SCRAP",
                total_items=1,
                total_weight=Decimal("10.0"),
                total_amount=Money(Decimal("250.0"), "MXN"),
                created_by=ids["user_id"],
                external_reference=doc_id.hex
            )
            session.add(doc_header)

            exit_mv = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=ids["warehouse_id"],
                product_id=ids["product_id"],
                company_id=ids["company_id"],
                quantity=Decimal("-20.0"),
                uom_id=ids["uom_id"],
                weight=Decimal("10.0"),
                movement_type="OUT",
                document_type="OUT",
                document_id=doc_id,
                concept_id=ids["concepts"].get("SAL-DIS"),
                price=Money(Decimal("12.50"), "MXN"),
                user_id=ids["user_id"],
                available_quantity=Decimal("0.0")
            )

            print("\n[OUT] Registrando salida de inventario...")
            await SQLAlchemyInventoryRepository(session).record_movement(exit_mv)
            await session.commit()

            print(f"OK  Salida registrada.")
            print(f"    Movement ID : {exit_mv.id}")
            print(f"    Tipo        : {exit_mv.movement_type}")
            print(f"    Cantidad    : {exit_mv.quantity} PZ (descuento)")
            print(f"    Producto    : {ids['product_id']} (SKU-PROD-01)")

    except RuntimeError as e:
        print(f"\nERROR: {e}")
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_flow_2())
