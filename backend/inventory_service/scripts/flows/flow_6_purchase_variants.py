import asyncio
import uuid
import sys
import os
from decimal import Decimal
from datetime import datetime, timezone

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from app.db.session import AsyncSessionLocal
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.models.document import InventoryDocument, DocumentStatus
from app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money
from sqlalchemy import text

# ─── CONFIGURACIÓN ───
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
WH_ENTERPRISE_TJ_ID = uuid.UUID("fd76bbe3-6d6f-5e74-ae15-d605acbc2289")
USER_A_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
UOM_ID = uuid.UUID("1a7444c9-40df-51d5-833b-501fc84b67bb")

async def record_bulk_purchases():
    print("==================================================")
    print("🚀 FLUJO 6: COMPRA MASIVA DE VARIANTES (ENTRY)")
    print(f"🏢 Empresa: Interno Enterprise")
    print(f"📍 Almacén: {WH_ENTERPRISE_TJ_ID}")
    print("==================================================")
    
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyInventoryRepository(session)
        
        # 1. Obtener todas las variantes de la empresa
        res = await session.execute(text("""
            SELECT id, product_id, internal_sku, brand, mfg_part_number, unit_price 
            FROM inventory_item_variants 
            WHERE company_id = :co_id
        """), {"co_id": CO_ENTERPRISE_ID})
        
        variants = res.fetchall()
        if not variants:
            print("❌ No se encontraron variantes. Por favor corre seed_variants.py primero.")
            return

        print(f"📦 Procesando compra para {len(variants)} variantes...")

        # 2. Crear Cabecera de Documento de Compra
        doc_id = uuid.uuid4()
        total_amount = Decimal("0.0")
        
        # Calculamos totales para la cabecera
        for v in variants:
            total_amount += v.unit_price * Decimal("100.0") # Compramos 100 de cada una

        doc_header = InventoryDocument(
            id=doc_id,
            company_id=CO_ENTERPRISE_ID,
            tenant_id=CO_ENTERPRISE_ID,
            folio=f"PURCHASE-{doc_id.hex[:6].upper()}",
            document_type="ENTRY",
            status=DocumentStatus.PROCESSED,
            origin_name="SUPPLIER_GLOBAL",
            destination_name="MAIN_WAREHOUSE",
            total_items=len(variants),
            total_amount=Money(total_amount, "USD"),
            total_weight=Decimal(len(variants)) * Decimal("1.5"), # Peso dummy
            created_by=USER_A_ID,
            external_reference=f"PO-{doc_id.hex[:8].upper()}"
        )
        
        session.add(doc_header)
        await session.flush()
        
        print(f"📄 Documento creado: {doc_header.folio} | Ref: {doc_header.external_reference}")

        # 3. Registrar Movimientos de cada Variante
        for v in variants:
            qty = Decimal("100.0")
            price = v.unit_price
            
            entry_mv = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=WH_ENTERPRISE_TJ_ID,
                product_id=v.product_id,
                variant_id=v.id,
                company_id=CO_ENTERPRISE_ID,
                quantity=qty,
                uom_id=UOM_ID,
                weight=Decimal("1.5"),
                movement_type="IN",
                document_type="ENTRY",
                document_id=doc_id,
                price=Money(price, "USD"),
                user_id=USER_A_ID,
                available_quantity=qty # Capa de stock para FIFO
            )
            
            await repo.record_movement(entry_mv)
            print(f"   ↳ [OK] SKU: {v.internal_sku} | Brand: {v.brand} | MPN: {v.mfg_part_number} | Qty: {qty}")

        await session.commit()
        print("\n✅ Compra masiva registrada exitosamente en el Kardex.")

if __name__ == "__main__":
    asyncio.run(record_bulk_purchases())
