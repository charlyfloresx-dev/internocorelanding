import asyncio
import uuid
import sys
import os
import traceback
from decimal import Decimal

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from app.db.session import AsyncSessionLocal
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from app.domain.entities.transfer_entities import InitiateTransferCommand, CompleteTransferCommand

# ─── REAL DATABASE IDS ───
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
CO_LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")

WH_ENTERPRISE_TJ_ID = uuid.UUID("fd76bbe3-6d6f-5e74-ae15-d605acbc2289")
WH_LOGISTICS_MX_TJ_ID = uuid.UUID("ce699eae-5db7-5d0a-a808-fd57a400523a")

PROD_ID = uuid.UUID("133ec1c3-36eb-5977-a281-e0e6e5092d5e")
UOM_ID = uuid.UUID("1a7444c9-40df-51d5-833b-501fc84b67bb")

USER_A_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38") # Enterprise
USER_B_ID = uuid.UUID("74125896-1234-4bc1-bbaa-123456789abc") # Logistics MX

async def ensure_warehouses(session):
    from sqlalchemy import text
    from datetime import datetime, timezone
    now_tz = datetime.now(timezone.utc)
    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code, is_active, 
            version_id, is_transit, created_at
        )
        VALUES (
            :id, 'Enterprise Main TJ', :co_id, :co_id, 'ENT-MAIN', 'MX', TRUE, 
            1, FALSE, :now_tz
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_ENTERPRISE_TJ_ID, "co_id": CO_ENTERPRISE_ID, "now_tz": now_tz})

    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code, is_active, 
            version_id, is_transit, created_at
        )
        VALUES (
            :id, 'Logistics MX TJ', :co_id, :co_id, 'LOG-MX', 'MX', TRUE, 
            1, FALSE, :now_tz
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_LOGISTICS_MX_TJ_ID, "co_id": CO_LOGISTICS_MX_ID, "now_tz": now_tz})

async def run_flow_4():
    print("==================================================")
    print("🚀 FLUJO 4: TRANSFERENCIA INTER-COMPANY (NACIONAL)")
    print("🏢 Origen: Interno Enterprise (MX) -> Destino: Interno Logistics (MX)")
    print("==================================================")
    
    try:
        async with AsyncSessionLocal() as session:
            await ensure_warehouses(session)
            await session.commit()
            
            repo = SQLAlchemyInventoryRepository(session)
            handler = TransferCommandHandler(session, repo)
            
            print("\n[🚚] Iniciando venta/traslado entre empresas (Enterprise despacha)...")
            ict_mx_cmd = InitiateTransferCommand(
                origin_company_id=CO_ENTERPRISE_ID,
                destination_company_id=CO_LOGISTICS_MX_ID,  # Diferente empresa
                origin_warehouse_id=WH_ENTERPRISE_TJ_ID,
                destination_warehouse_id=WH_LOGISTICS_MX_TJ_ID,
                product_id=PROD_ID,
                quantity=Decimal("25.0"),
                weight=Decimal("12.5"),
                uom_id=UOM_ID,
                initiated_by=USER_A_ID,
                transfer_price=Decimal("15.75"), # El precio pactado inter-company
                customs_pedimento="244030001234567" # Pedimento semilla para operaciones originadas por importación
            )
            
            transfer = await handler.initiate_transfer(ict_mx_cmd)
            await session.commit()
            print(f"✅ Transferencia enviada (En Tránsito). Folio ICT: {transfer.folio}")
            
            print("\n[📦] Efectuando recepción (Logistics MX recibe)...")
            ict_mx_receive = CompleteTransferCommand(
                transfer_id=transfer.id,
                received_by=USER_B_ID,
                receiver_company_id=CO_LOGISTICS_MX_ID, 
                received_quantity=Decimal("25.0")
            )
            
            await handler.complete_transfer(ict_mx_receive)
            await session.commit()
            print(f"✅ Recepción validada en Kardex B. Stock en Tránsito descontado.")
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_flow_4())
