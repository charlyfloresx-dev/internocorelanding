
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
from app.api.v1.handlers.transfer_command_handler import TransferCommandHandler
from app.domain.entities.transfer_entities import (
    InitiateTransferCommand,
    CompleteTransferCommand,
)
from app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money

# ─── REAL DATABASE IDS (Synced with Seed) ───
CO_ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
CO_LOGISTICS_MX_ID = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")
CO_LOGISTICS_US_ID = uuid.UUID("777cc8a6-34f9-42df-8f29-28254e0ad277")

WH_ENTERPRISE_TJ_ID = uuid.UUID("fd76bbe3-6d6f-5e74-ae15-d605acbc2289") 
WH_LOGISTICS_MX_TJ_ID = uuid.UUID("ce699eae-5db7-5d0a-a808-fd57a400523a") 
WH_LOGISTICS_US_SD_ID = uuid.UUID("de06c646-34f9-42df-8f29-28254e0ad242") 

# Aluminum Coil 
PROD_ID = uuid.UUID("133ec1c3-36eb-5977-a281-e0e6e5092d5e") 
UOM_ID = uuid.UUID("1a7444c9-40df-51d5-833b-501fc84b67bb") 

# ─── PHASE 40 USERS (SoD Compliant) ───
USER_A_ID = uuid.UUID("69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38") # Charly (Enterprise Admin)
USER_B_ID = uuid.UUID("74125896-1234-4bc1-bbaa-123456789abc") # Operator (Logistics MX)
USER_C_ID = uuid.UUID("85236974-5678-4cd2-ccbb-987654321def") # Supervisor (Logistics US)

# Fixed 15-char pedimento
PEDIMENTO_NUM = "244030001234567"
PED_ID = uuid.uuid4()

async def ensure_u_s_warehouse(session):
    from sqlalchemy import text
    now_tz = datetime.now(timezone.utc)
    print("Ensuring US Warehouse (SD)...")
    await session.execute(text("""
        INSERT INTO inventory_warehouses (
            id, name, company_id, tenant_id, code, country_code, is_active, 
            version_id, is_transit, created_at
        )
        VALUES (
            :id, 'San Diego Hub', :co_id, :co_id, 'SD-US', 'US', TRUE, 
            1, FALSE, :now_tz
        )
        ON CONFLICT (id) DO NOTHING;
    """), {"id": WH_LOGISTICS_US_SD_ID, "co_id": CO_LOGISTICS_US_ID, "now_tz": now_tz})

async def ensure_pedimento(session):
    from sqlalchemy import text
    now_tz = datetime.now(timezone.utc)
    now_no_tz = datetime.now()
    print("Ensuring Seed Pedimento...")
    await session.execute(text("""
        INSERT INTO customs_pedimentos (
            id, pedimento_number, customs_key, customs_date, is_temporary, 
            operation_type, is_active, version_id, created_at, company_id, tenant_id
        )
        VALUES (
            :id, :num, 'A1', CAST(:now_no_tz AS TIMESTAMP), FALSE, 'IMPORT', TRUE, 1, CAST(:now_tz AS TIMESTAMPTZ), :co_id, :co_id
        )
        ON CONFLICT (pedimento_number) DO NOTHING;
    """), {
        "id": PED_ID, 
        "num": PEDIMENTO_NUM, 
        "now_no_tz": now_no_tz, 
        "now_tz": now_tz, 
        "co_id": CO_ENTERPRISE_ID
    })
    
    res = await session.execute(text("SELECT id FROM customs_pedimentos WHERE pedimento_number = :num"), {"num": PEDIMENTO_NUM})
    return res.scalar()

async def run_test():
    print("--- STARTING THREE-LEG BINATIONAL TRANSFER TEST (3-USER SoD) ---")
    try:
        async with AsyncSessionLocal() as session:
            await ensure_u_s_warehouse(session)
            actual_ped_id = await ensure_pedimento(session)
            await session.commit()
            
            repo = SQLAlchemyInventoryRepository(session)
            handler = TransferCommandHandler(session, repo)

            # 0. INJECT STOCK IN ENTERPRISE
            print("\nStep 0: Injecting seed stock (User A)...")
            entry_mv = MovementEntity(
                id=uuid.uuid4(),
                warehouse_id=WH_ENTERPRISE_TJ_ID,
                product_id=PROD_ID,
                company_id=CO_ENTERPRISE_ID,
                quantity=Decimal("100.0"),
                uom_id=UOM_ID,
                weight=Decimal("50.0"),
                movement_type="IN",
                document_type="TEST_INJECT",
                document_id=uuid.uuid4(),
                price=Money(Decimal("10.0"), "MXN"),
                user_id=USER_A_ID,
                customs_pedimento_id=actual_ped_id,
                available_quantity=Decimal("100.0")
            )
            await repo.record_movement(entry_mv)
            await session.commit()

            # ──────────────────────────────────────────────────────────────────
            # LEG 1: Enterprise TJ -> Logistics MX TJ
            # ──────────────────────────────────────────────────────────────────
            print("\nStep 1: User A ships Leg 1...")
            ict1_cmd = InitiateTransferCommand(
                origin_company_id=CO_ENTERPRISE_ID,
                destination_company_id=CO_LOGISTICS_MX_ID,
                origin_warehouse_id=WH_ENTERPRISE_TJ_ID,
                destination_warehouse_id=WH_LOGISTICS_MX_TJ_ID,
                product_id=PROD_ID,
                quantity=Decimal("10.0"),
                weight=Decimal("5.0"),
                uom_id=UOM_ID,
                initiated_by=USER_A_ID,
                transfer_price=Decimal("15.0"),
                customs_pedimento=PEDIMENTO_NUM
            )
            ict1 = await handler.initiate_transfer(ict1_cmd)
            await session.commit()
            print(f"Leg 1 SHIPPED. Folio: {ict1.folio}")

            print("\nStep 2: User B receives Leg 1...")
            ict1_in_cmd = CompleteTransferCommand(
                transfer_id=ict1.id,
                received_by=USER_B_ID,
                receiver_company_id=CO_LOGISTICS_MX_ID,
                received_quantity=Decimal("10.0")
            )
            await handler.complete_transfer(ict1_in_cmd)
            await session.commit()
            print("Leg 1 RECEIVED by User B.")

            # ──────────────────────────────────────────────────────────────────
            # LEG 2: Logistics MX TJ -> Logistics US SD (BINATIONAL)
            # ──────────────────────────────────────────────────────────────────
            print("\nStep 3: User B ships Leg 2 (BINATIONAL)...")
            ict2_cmd = InitiateTransferCommand(
                origin_company_id=CO_LOGISTICS_MX_ID,
                destination_company_id=CO_LOGISTICS_US_ID,
                origin_warehouse_id=WH_LOGISTICS_MX_TJ_ID,
                destination_warehouse_id=WH_LOGISTICS_US_SD_ID,
                product_id=PROD_ID,
                quantity=Decimal("5.0"),
                weight=Decimal("2.5"),
                uom_id=UOM_ID,
                initiated_by=USER_B_ID,
                transfer_price=None, # Trigger Finance administrative debt
                exchange_rate_dof=Decimal("20.1500"),
                risk_acknowledged=True,
                customs_pedimento=PEDIMENTO_NUM
            )
            ict2 = await handler.initiate_transfer(ict2_cmd)
            await session.commit()
            print(f"Leg 2 SHIPPED. Folio: {ict2.folio}")

            print("\nStep 4: User C receives Leg 2 in US...")
            ict2_in_cmd = CompleteTransferCommand(
                transfer_id=ict2.id,
                received_by=USER_C_ID,
                receiver_company_id=CO_LOGISTICS_US_ID,
                received_quantity=Decimal("5.0")
            )
            await handler.complete_transfer(ict2_in_cmd)
            await session.commit()
            print(f"Leg 2 RECEIVED by User C [SoD Compliant].")

            print("\n--- THREE-LEG ICT CYCLE COMPLETED SUCCESSFULLY ---")
            print(f"Validation Summary:")
            print(f"  - Leg 1: Admin A -> Op B [Internal MX-MX]")
            print(f"  - Leg 2: Op B -> Supervisor C [Binational MX-US]")
            print(f"  - Compliance: {ict2.pending_financial_valuation=}")
            
    except Exception as e:
        print(f"\n--- FATAL ERROR ---")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
