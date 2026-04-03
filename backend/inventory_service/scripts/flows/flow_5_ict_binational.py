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
CO_LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
CO_LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")

WH_LOGISTICS_MX_TJ_ID = uuid.UUID("ce699eae-5db7-5d0a-a808-fd57a400523a")
WH_LOGISTICS_US_SD_ID = uuid.UUID("de06c646-34f9-42df-8f29-28254e0ad242")

PROD_ID = uuid.UUID("133ec1c3-36eb-5977-a281-e0e6e5092d5e")
UOM_ID = uuid.UUID("1a7444c9-40df-51d5-833b-501fc84b67bb")

USER_B_ID = uuid.UUID("74125896-1234-4bc1-bbaa-123456789abc") # Logistics MX Operator
USER_C_ID = uuid.UUID("85236974-5678-4cd2-ccbb-987654321def") # Logistics US Supervisor

async def ensure_dependencies(session):
    from sqlalchemy import text
    from datetime import datetime, timezone
    now_tz = datetime.now(timezone.utc)
    now_no_tz = datetime.now()
    
    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code, is_active, 
            version_id, is_transit, created_at
        )
        VALUES (
            :id, 'Logistics MX TJ', :co_mx, :co_mx, 'LOG-MX', 'MX', TRUE, 
            1, FALSE, :now_tz
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_LOGISTICS_MX_TJ_ID, "co_mx": CO_LOGISTICS_MX_ID, "now_tz": now_tz})

    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code, is_active, 
            version_id, is_transit, created_at
        )
        VALUES (
            :id, 'Logistics US SD', :co_us, :co_us, 'LOG-US', 'US', TRUE, 
            1, FALSE, :now_tz
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_LOGISTICS_US_SD_ID, "co_us": CO_LOGISTICS_US_ID, "now_tz": now_tz})

    await session.execute(text("""
        INSERT INTO customs_pedimentos (
            id, pedimento_number, customs_key, customs_date, is_temporary, 
            operation_type, is_active, version_id, created_at, company_id, tenant_id
        )
        VALUES (
            :id, '244030001234567', 'A1', CAST(:now_no_tz AS TIMESTAMP), FALSE, 'IMPORT', TRUE, 1, CAST(:now_tz AS TIMESTAMPTZ), :co_mx, :co_mx
        )
        ON CONFLICT (pedimento_number) DO NOTHING;
    """), {
        "id": uuid.uuid4(), 
        "now_no_tz": now_no_tz, 
        "now_tz": now_tz, 
        "co_mx": CO_LOGISTICS_MX_ID
    })

async def run_flow_5():
    print("==================================================")
    print("🚀 FLUJO 5: TRANSFERENCIA BINACIONAL (INTER-COMPANY CROSS-BORDER)")
    print("🏢 Origen: Interno Logistics (MX) -> Destino: Interno Logistics (US)")
    print("==================================================")
    
    try:
        async with AsyncSessionLocal() as session:
            await ensure_dependencies(session)
            await session.commit()
            
            repo = SQLAlchemyInventoryRepository(session)
            handler = TransferCommandHandler(session, repo)
            
            print("\n[🚚] Exportación iniciada (Logistics MX despacha a frontera)...")
            ict_binational_cmd = InitiateTransferCommand(
                origin_company_id=CO_LOGISTICS_MX_ID,
                destination_company_id=CO_LOGISTICS_US_ID,  # Diferente país
                origin_warehouse_id=WH_LOGISTICS_MX_TJ_ID,
                destination_warehouse_id=WH_LOGISTICS_US_SD_ID,
                product_id=PROD_ID,
                quantity=Decimal("5.0"),
                weight=Decimal("2.5"),
                uom_id=UOM_ID,
                initiated_by=USER_B_ID,
                transfer_price=None, # Financieramente transitorio (precio heredado o deuda pendiente)
                exchange_rate_dof=Decimal("20.1500"), # Importante para la contabilidad MX
                risk_acknowledged=True, # Cumplimiento de Anexo 24 validado por usuario
                customs_pedimento="244030001234567" # EL PEDIMENTO ES OBLIGATORIO en MX -> US
            )
            
            transfer = await handler.initiate_transfer(ict_binational_cmd)
            await session.commit()
            print(f"✅ Cruce registrado en puerto de salida (En Tránsito Binacional). Folio: {transfer.folio}")
            
            print("\n[📦] Aduana completada, recepción en almacén de EEUU (Logistics US)...")
            ict_binational_receive = CompleteTransferCommand(
                transfer_id=transfer.id,
                received_by=USER_C_ID,
                receiver_company_id=CO_LOGISTICS_US_ID, 
                received_quantity=Decimal("5.0")
            )
            
            await handler.complete_transfer(ict_binational_receive)
            await session.commit()
            print(f"✅ Mercancía dada de alta en inventario de EEUU. Tránsito cerrado correctamente.")
            print(f"   [!] Se requiere valuación financiera posterior para deudas Inter-Company ({transfer.pending_financial_valuation}).")
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_flow_5())
