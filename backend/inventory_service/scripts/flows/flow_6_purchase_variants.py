"""
flow_6_purchase_variants.py
------------------------------
Flujo 6: Entrada masiva de inventario por variantes de producto.
Registra 100 PZ por cada variante existente en la empresa Enterprise.

Pre-requisito: seed_variants.py ejecutado primero para crear las variantes.
               flow_1_entry.py no es necesario (este flujo es independiente).
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
from inventory_app.models.document import InventoryDocument, DocumentStatus
from inventory_app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money
from flows._shared_ids import resolve_flow_ids


async def record_bulk_purchases():
    print("=" * 55)
    print("FLUJO 6: ENTRADA MASIVA POR VARIANTES")
    print("Empresa: Interno Enterprise")
    print("=" * 55)

    try:
        async with AsyncSessionLocal() as session:
            ids = await resolve_flow_ids(session)

            # Cargar variantes existentes de la empresa
            res = await session.execute(text("""
                SELECT id, product_id, internal_sku, brand, mfg_part_number, unit_price
                FROM inventory_item_variants
                WHERE company_id = :co_id
            """), {"co_id": ids["company_id"]})

            variants = res.fetchall()
            if not variants:
                print("SKIP: No se encontraron variantes.")
                print("      Ejecuta primero: python scripts/flows/seed_variants.py")
                return

            print(f"INFO: Procesando entrada para {len(variants)} variante(s)...")

            # Cabecera de documento
            doc_id = uuid.uuid4()
            total_amount = sum(v.unit_price * Decimal("100.0") for v in variants)

            doc_header = InventoryDocument(
                id=doc_id,
                company_id=ids["company_id"],
                tenant_id=ids["company_id"],
                folio=f"PURCHASE-{doc_id.hex[:6].upper()}",
                document_type="ENTRY",
                status=DocumentStatus.PROCESSED,
                origin_name="SUPPLIER_GLOBAL",
                destination_name="MAIN_WAREHOUSE",
                total_items=len(variants),
                total_amount=Money(total_amount, "USD"),
                total_weight=Decimal(len(variants)) * Decimal("1.5"),
                created_by=ids["user_id"],
                external_reference=f"PO-{doc_id.hex[:8].upper()}"
            )
            session.add(doc_header)
            await session.flush()

            print(f"INFO: Documento creado: {doc_header.folio} | PO Ref: {doc_header.external_reference}")

            # Registrar movimiento por cada variante
            repo = SQLAlchemyInventoryRepository(session)
            for v in variants:
                qty = Decimal("100.0")
                entry_mv = MovementEntity(
                    id=uuid.uuid4(),
                    warehouse_id=ids["warehouse_id"],
                    product_id=v.product_id,
                    variant_id=v.id,
                    company_id=ids["company_id"],
                    quantity=qty,
                    uom_id=ids["uom_id"],
                    weight=Decimal("1.5"),
                    movement_type="IN",
                    document_type="ENTRY",
                    document_id=doc_id,
                    price=Money(v.unit_price, "USD"),
                    user_id=ids["user_id"],
                    available_quantity=qty
                )
                await repo.record_movement(entry_mv)
                print(f"    OK  SKU: {v.internal_sku} | {v.brand} | qty: {qty}")

            await session.commit()
            print(f"\nOK  Entrada masiva registrada ({len(variants)} variantes).")

    except RuntimeError as e:
        print(f"\nERROR: {e}")
    except Exception:
        print("\nFATAL ERROR")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(record_bulk_purchases())
