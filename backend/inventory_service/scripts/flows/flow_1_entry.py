"""
flow_1_entry.py
-----------------
Flujo 1: Entrada de inventario (IN).
Registra 150 unidades del producto SKU-PROD-01 en el almacen WH-001.

Pre-requisito: unified_industrial_seed.py ejecutado correctamente.
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


async def run_flow_1():
    print("=" * 50)
    print("FLUJO 1: ENTRADA DE INVENTARIO (IN)")
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
                folio=f"IN-{doc_id.hex[:6].upper()}",
                document_type="IN",
                status=DocumentStatus.PROCESSED,
                origin_name="EXTERNAL VENDOR",
                destination_name="STOCK",
                total_items=1,
                total_weight=Decimal("75.0"),
                total_amount=Money(Decimal("1875.0"), "MXN"),
                created_by=ids["user_id"],
                external_reference=doc_id.hex
            )
            session.add(doc_header)

            entry_mv = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=ids["warehouse_id"],
                product_id=ids["product_id"],
                company_id=ids["company_id"],
                quantity=Decimal("150.0"),
                uom_id=ids["uom_id"],
                weight=Decimal("75.0"),
                movement_type="IN",
                document_type="IN",
                document_id=doc_id,
                price=Money(Decimal("12.50"), "MXN"),
                user_id=ids["user_id"],
                available_quantity=Decimal("150.0")
            )

            print("\n[IN] Registrando entrada de inventario...")
            await SQLAlchemyInventoryRepository(session).record_movement(entry_mv)
            await session.commit()

            print(f"OK  Entrada registrada.")
            print(f"    Movement ID : {entry_mv.id}")
            print(f"    Tipo        : {entry_mv.movement_type}")
            print(f"    Cantidad    : {entry_mv.quantity} PZ")
            print(f"    Precio unit : $12.50 MXN")
            print(f"    Almacen     : {ids['warehouse_id']}")
            print(f"    Producto    : {ids['product_id']} (SKU-PROD-01)")

    except RuntimeError as e:
        print(f"\nERROR: {e}")
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_flow_1())
