import asyncio
import uuid
import sys
import os
import traceback
from decimal import Decimal
from datetime import datetime, timezone

if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from app.domain.entities.transfer_entities import InitiateTransferCommand, CompleteTransferCommand

# ─── REAL DATABASE IDS ───
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
WH_ENTERPRISE_TJ_ID = uuid.UUID("fd76bbe3-6d6f-5e74-ae15-d605acbc2289")
PROD_ID = uuid.UUID("133ec1c3-36eb-5977-a281-e0e6e5092d5e")
UOM_ID = uuid.UUID("1a7444c9-40df-51d5-833b-501fc84b67bb")
USER_A_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38")
USER_B_ID = uuid.UUID("74125896-1234-4bc1-bbaa-123456789abc")

# Creamos un Warehouse Secundario al Vuelo
WH_ENTERPRISE_TJ_2_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "interno.warehouse.ENTERPRISE-SECONDARY")

async def ensure_secondary_warehouse(session):
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

    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code, type, is_active, 
            version_id, is_transit, created_at
        )
        VALUES (
            :id, 'Enterprise Secondary TJ', :co_id, :co_id, 'ENT-SEC', 'MX', 'PHYSICAL', TRUE, 
            1, FALSE, :now_tz
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_ENTERPRISE_TJ_2_ID, "co_id": CO_ENTERPRISE_ID, "now_tz": now_tz})

async def run_flow_3():
    print("==================================================")
    print("🚀 FLUJO 3: TRANSFERENCIA INTERNA")
    print("🏢 Empresa: Interno Enterprise -> Interno Enterprise")
    print("==================================================")
    
    try:
        async with AsyncSessionLocal() as session:
            await ensure_secondary_warehouse(session)
            await session.commit()
            
            repo = SQLAlchemyInventoryRepository(session)
            handler = TransferCommandHandler(session, repo)
            
            print("\n[🚚] Iniciando envío interno (Despacho)...")
            ict_internal_cmd = InitiateTransferCommand(
                origin_company_id=CO_ENTERPRISE_ID,
                destination_company_id=CO_ENTERPRISE_ID,  # Misma empresa
                origin_warehouse_id=WH_ENTERPRISE_TJ_ID,
                destination_warehouse_id=WH_ENTERPRISE_TJ_2_ID,
                product_id=PROD_ID,
                quantity=Decimal("15.0"),
                weight=Decimal("7.5"),
                uom_id=UOM_ID,
                initiated_by=USER_A_ID,
                transfer_price=None, # Transferencia de mismo valor, respeta WAC actual
                customs_pedimento=None # Misma entidad, origen nacional, no ocupa pedimento
            )
            
            transfer = await handler.initiate_transfer(ict_internal_cmd)
            await session.commit()
            print(f"✅ Despacho registrado. Estado: SHIPPED. Folio: {transfer.folio}")
            
            print("\n[📦] Efectuando recepción interna (Receive)...")
            ict_internal_receive = CompleteTransferCommand(
                transfer_id=transfer.id,
                received_by=USER_B_ID,
                receiver_company_id=CO_ENTERPRISE_ID, # Misma empresa
                received_quantity=Decimal("15.0")
            )
            
            await handler.complete_transfer(ict_internal_receive)
            await session.commit()
            print(f"✅ Recepción exitosa en almacén destino. Transferencia COMPLETADA.")
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_flow_3())
