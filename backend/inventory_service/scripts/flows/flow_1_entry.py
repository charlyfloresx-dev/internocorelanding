import asyncio
import uuid
import sys
import os
import traceback
from decimal import Decimal
from datetime import datetime, timezone

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from app.db.session import AsyncSessionLocal
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money
from app.models.document import InventoryDocument, DocumentStatus

# ─── REAL DATABASE IDS ───
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
WH_ENTERPRISE_TJ_ID = uuid.UUID("fd76bbe3-6d6f-5e74-ae15-d605acbc2289")
PROD_ID = uuid.UUID("133ec1c3-36eb-5977-a281-e0e6e5092d5e")
UOM_ID = uuid.UUID("1a7444c9-40df-51d5-833b-501fc84b67bb")
USER_A_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")

async def ensure_warehouse(session):
    from sqlalchemy import text
    now_tz = datetime.now(timezone.utc)
    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code, type, is_active, 
            version_id, is_transit, created_at
        )
        VALUES (
            :id, 'Enterprise Main TJ', :co_id, :co_id, 'ENT-MAIN', 'MX', 'PHYSICAL', TRUE, 
            1, FALSE, :now_tz
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_ENTERPRISE_TJ_ID, "co_id": CO_ENTERPRISE_ID, "now_tz": now_tz})

async def run_flow_1():
    print("==================================================")
    print("🚀 FLUJO 1: ENTRADA DE INVENTARIO (IN)")
    print("🏢 Empresa: Interno Enterprise")
    print("==================================================")
    
    try:
        async with AsyncSessionLocal() as session:
            await ensure_warehouse(session)
            await session.commit()
            
            repo = SQLAlchemyInventoryRepository(session)
            
            doc_id = uuid.uuid4()
            
            # Create Document Header for traceability in dashboard
            doc_header = InventoryDocument(
                id=doc_id,
                company_id=CO_ENTERPRISE_ID,
                tenant_id=CO_ENTERPRISE_ID,
                folio=f"IN-MANUAL-{doc_id.hex[:6].upper()}",
                document_type="IN",
                status=DocumentStatus.PROCESSED,
                origin_name="EXTERNAL VENDOR",
                destination_name="STOCK",
                total_items=1,
                total_weight=Decimal("75.0"),
                total_amount=Money(Decimal("1875.0"), "MXN"),
                created_by=USER_A_ID,
                external_reference=doc_id.hex
            )
            session.add(doc_header)

            entry_mv = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=WH_ENTERPRISE_TJ_ID,
                product_id=PROD_ID,
                company_id=CO_ENTERPRISE_ID,
                quantity=Decimal("150.0"),
                uom_id=UOM_ID,
                weight=Decimal("75.0"),
                movement_type="IN",
                document_type="IN",
                document_id=doc_id, # Link to header
                price=Money(Decimal("12.50"), "MXN"),
                user_id=USER_A_ID,
                available_quantity=Decimal("150.0")
            )
            
            print("\n[➡️ ] Registrando entrada de inventario...")
            await repo.record_movement(entry_mv)
            await session.commit()
            
            print(f"✅ Entrada registrada exitosamente.")
            print(f"   ↳ ID Movimiento: {entry_mv.id}")
            print(f"   ↳ Tipo: {entry_mv.movement_type}")
            print(f"   ↳ Cantidad: {entry_mv.quantity} (Stock Incremental)")
            print(f"   ↳ Precio Unitario: $12.50 MXN")
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_flow_1())
