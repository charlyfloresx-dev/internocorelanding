import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

import sys
import os
# Add backend to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.movement import Movement
from app.models.customs_pedimento import CustomsPedimento, CustomsOperationType
from app.models.inventory import InventoryLevel
from app.models.warehouse import Warehouse
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.domain.entities.inventory_item import MovementEntity
from common.domain.value_objects import Money

# DB_URL for local testing (matches dev environment defined in docker-compose.yml host mapping)
DB_URL = "postgresql+asyncpg://user:password@localhost:5433/inventory_db"

async def test_fifo_logic():
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        repo = SQLAlchemyInventoryRepository(session)
        company_id = uuid.uuid4()
        user_id = str(uuid.uuid4())
        warehouse_id = uuid.uuid4()
        product_id = uuid.uuid4()
        
        # 0. Sync Warehouse to avoid ownership errors
        # In this test, we skip master-data sync and insert directly
        wh = Warehouse(
            id=warehouse_id, 
            company_id=company_id, 
            tenant_id=company_id, 
            code="TEST-FIFO", 
            name="FIFO Audit Warehouse",
            country_code="MX",
            created_by=user_id,
            updated_by=user_id
        )
        session.add(wh)
        await session.flush()
        
        print(f"--- [FIFO TEST] Created context for Product {product_id} ---")
        
        # 1. Setup 2 Pedimentos with different customs dates (Naive for naive columns)
        ped1_id = uuid.uuid4()
        ped1 = CustomsPedimento(
            id=ped1_id,
            company_id=company_id,
            tenant_id=company_id,
            pedimento_number="210134567800001",
            customs_key="AF",
            operation_type=CustomsOperationType.IMPORT,
            customs_date=datetime.now() - timedelta(days=10),
            is_temporary=True,
            created_by=user_id,
            updated_by=user_id
        )
        
        ped2_id = uuid.uuid4()
        ped2 = CustomsPedimento(
            id=ped2_id,
            company_id=company_id,
            tenant_id=company_id,
            pedimento_number="210134567800002",
            customs_key="AF",
            operation_type=CustomsOperationType.IMPORT,
            customs_date=datetime.now() - timedelta(days=2),
            is_temporary=True,
            created_by=user_id,
            updated_by=user_id
        )
        session.add_all([ped1, ped2])
        await session.flush()
        
        # 2. Setup 2 entries (50 units each)
        entry1 = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=Decimal("50.0"),
            available_quantity=Decimal("50.0"),
            customs_pedimento_id=ped1_id,
            uom_id=uuid.uuid4(),
            weight=Decimal("10.0"),
            price=Money(Decimal("100.0"), "USD"),
            movement_type="IN",
            document_type="TEST_ENTRY",
            document_id=uuid.uuid4(),
            user_id=user_id,
            expiry_date=datetime.now() + timedelta(days=500)
        )
        
        entry2 = MovementEntity(
            id=uuid.uuid4(),
            warehouse_id=warehouse_id,
            product_id=product_id,
            company_id=company_id,
            quantity=Decimal("50.0"),
            available_quantity=Decimal("50.0"),
            customs_pedimento_id=ped2_id,
            uom_id=uuid.uuid4(),
            weight=Decimal("10.0"),
            price=Money(Decimal("105.0"), "USD"),
            movement_type="IN",
            document_type="TEST_ENTRY",
            document_id=uuid.uuid4(),
            user_id=user_id,
            expiry_date=datetime.now() + timedelta(days=600)
        )
        
        await repo.record_movement(entry1)
        await repo.record_movement(entry2)
        await session.commit()
        print("Initial state: 2 layers of 50 units (FIFO Ready).")
        
        # 3. Simulate exits using the real Domain Service
        from app.domain.services.fifo_discharge_service import FIFODischargeService
        
        print("Executing 4 partial exits (15 units each) to force layer transition...")
        total_requested = Decimal("0")
        for i in range(4):
            requested_qty = Decimal("15.0")
            total_requested += requested_qty
            
            # Start a sub-transaction per exit
            async with session.begin_nested():
                plan = await FIFODischargeService.get_discharge_plan(
                    session=session,
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    requested_qty=requested_qty,
                    company_id=str(company_id)
                )
                
                for instr in plan:
                    # Apply discharge at DB level
                    await session.execute(
                        Movement.__table__.update()
                        .where(Movement.id == instr.source_movement_id)
                        .values(available_quantity=Movement.available_quantity - instr.quantity_to_discharge)
                    )
                    print(f"  [DISCHARGE] i={i}: Consumed {instr.quantity_to_discharge} from Pedimento {instr.customs_pedimento_id}")
                    
                    # Record OUT movement (simulated)
                    out_mov = Movement(
                        id=uuid.uuid4(),
                        warehouse_id=warehouse_id,
                        product_id=product_id,
                        company_id=company_id,
                        tenant_id=company_id,
                        quantity=-instr.quantity_to_discharge,
                        uom_id=uuid.uuid4(),
                        weight=Decimal("2.0"),
                        movement_type="OUT",
                        document_type="TEST_OUT",
                        document_id=uuid.uuid4(),
                        source_movement_id=instr.source_movement_id,
                        customs_pedimento_id=instr.customs_pedimento_id,
                        created_by=user_id,
                        updated_by=user_id
                    )
                    session.add(out_mov)
            
        await session.commit()
        print(f"Total Exit: {total_requested} units. Expected Balance: 40 units remaining on Ped 2.")
        
        # 4. Verify via the Report repository method
        report = await repo.get_customs_balances(company_id=company_id)
        
        print("\n--- [CUSTOMS BALANCE REPORT] ---")
        for line in report:
            print(f"Pedimento: {line['pedimento_number']} | Qty: {line['total_available_qty']} | Risk: {line['is_at_risk']}")
            
        # Expected Verification
        if len(report) == 1:
            line = report[0]
            if line['pedimento_number'] == "210134567800002" and line['total_available_qty'] == Decimal("40.0"):
                print("✅ [VERIFIED] FIFO Correctly exhausted Ped 1 and left 40 in Ped 2.")
            else:
                print(f"❌ [FAILED] Unexpected balance: {line['total_available_qty']} in {line['pedimento_number']}")
        else:
            print(f"❌ [FAILED] Expected 1 line in report, got {len(report)}")
        
        if len(report) == 0:
            print("SUCCESS: 0 lines returned (All stock consumed).")
        else:
            print(f"Report contains {len(report)} lines.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_fifo_logic())
