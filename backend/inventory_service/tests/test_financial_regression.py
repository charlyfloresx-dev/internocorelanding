import sys
import os
import uuid
import asyncio
import traceback
from decimal import Decimal

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
backend_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(backend_root)

from common.models import Base
from inventory_app.db.session import AsyncSessionLocal, engine
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.services.transfer_service import TransferService
from inventory_app.models.warehouse import Warehouse
from inventory_app.models.inventory import InventoryLevel
from inventory_app.domain.entities.inventory_item import MovementEntity

async def test_financial_regression():
    print("--- Starting Financial Regression Test (Transfers) ---")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 1. Setup Data
    company_src = uuid.uuid4()
    company_dest = uuid.uuid4() # Moving between different companies for stress test
    wh_src = uuid.uuid4()
    wh_dest = uuid.uuid4()
    product_id = uuid.uuid4()
    uom_id = uuid.uuid4()
    transfer_id = uuid.uuid4()
    
    async with AsyncSessionLocal() as db:
        repo = SQLAlchemyInventoryRepository(db)
        transfer_svc = TransferService(repo)
        
        try:
            # Create Warehouses
            db.add(Warehouse(id=wh_src, code="SRC", name="Source Warehouse", company_id=company_src))
            db.add(Warehouse(id=wh_dest, code="DEST", name="Dest Warehouse", company_id=company_dest))
            # Create Transit Warehouse (Destination's transit)
            transit_id = uuid.uuid5(uuid.NAMESPACE_OID, f"{wh_dest}_transit")
            db.add(Warehouse(id=transit_id, code="DEST-TRANS", name="Dest Transit", company_id=company_dest))
            await db.commit()
            
            # Initial Stock in Source: 100 units @ $10.00
            print("   Initializing Source: 100 units @ $10.00")
            m_init_src = MovementEntity(
                id=uuid.uuid4(), warehouse_id=wh_src, product_id=product_id,
                company_id=company_src, quantity=Decimal("100.0"), movement_type="IN",
                unit_price=Decimal("10.0"), uom_id=uom_id, weight=Decimal("10.0"),
                document_type="INITIAL", document_id=uuid.uuid4()
            )
            await repo.record_movement(m_init_src)
            
            # Initial Stock in Destination: 20 units @ $15.00
            print("   Initializing Destination: 20 units @ $15.00")
            m_init_dest = MovementEntity(
                id=uuid.uuid4(), warehouse_id=wh_dest, product_id=product_id,
                company_id=company_dest, quantity=Decimal("20.0"), movement_type="IN",
                unit_price=Decimal("15.0"), uom_id=uom_id, weight=Decimal("20.0"),
                document_type="INITIAL", document_id=uuid.uuid4()
            )
            await repo.record_movement(m_init_dest)
            await db.commit()
            
            # 2. Verify Initial Valuation
            val_src = await repo.get_wac_valuation(product_id, wh_src, company_src)
            val_dest = await repo.get_wac_valuation(product_id, wh_dest, company_dest)
            
            initial_total_value = val_src.total_inventory_value + val_dest.total_inventory_value
            print(f"   Initial Total Value: ${initial_total_value} (Src: ${val_src.total_inventory_value}, Dest: ${val_dest.total_inventory_value})")
            
            # 3. Perform Transfer: Dispatch 40 units
            print("\n   [STEP 1] Dispatching 40 units from Source to Transit...")
            await transfer_svc.dispatch_transfer(
                wh_src, wh_dest, product_id, Decimal("40.0"), uom_id, Decimal("4.0"), # assuming weight 0.1 per unit for test
                company_src, transfer_id
            )
            await db.commit()
            
            # Verify Value Preservation (Source + Destination Transit)
            val_src_after = await repo.get_wac_valuation(product_id, wh_src, company_src)
            # Note: We need to check valuation in transit as well. 
            # Since transit is DEST's company, we check it there.
            val_transit = await repo.get_wac_valuation(product_id, transit_id, company_dest)
            
            current_value_phase1 = val_src_after.total_inventory_value + val_dest.total_inventory_value + val_transit.total_inventory_value
            print(f"   Phase 1 Total Value: ${current_value_phase1} (Src: ${val_src_after.total_inventory_value}, Transit: ${val_transit.total_inventory_value})")
            
            # 4. Finalize Transfer: Receive 40 units
            print("\n   [STEP 2] Receiving 40 units at Destination...")
            # We must use company_dest for receiving
            await transfer_svc.receive_transfer(
                wh_src, wh_dest, product_id, Decimal("40.0"), uom_id, Decimal("4.0"),
                company_dest, transfer_id
            )
            await db.commit()
            
            # 5. Final Valuation Check
            val_src_final = await repo.get_wac_valuation(product_id, wh_src, company_src)
            val_dest_final = await repo.get_wac_valuation(product_id, wh_dest, company_dest)
            
            final_total_value = val_src_final.total_inventory_value + val_dest_final.total_inventory_value
            print(f"   Final Total Value: ${final_total_value} (Src: ${val_src_final.total_inventory_value}, Dest: ${val_dest_final.total_inventory_value})")
            
            # Check Math:
            # Src: 60 units @ $10.00 = $600.00
            # Dest: 20 units @ $15.00 + 40 units @ $10.00 = 300 + 400 = $700.00
            # Total: $1300.00
            # Expected Initial: (100 * 10) + (20 * 15) = 1000 + 300 = $1300.00
            
            if final_total_value == initial_total_value:
                print("   [PASS] Total Inventory Value preserved perfectly.")
            else:
                print(f"   [FAIL] Value mismatch! Diff: ${final_total_value - initial_total_value}")
                sys.exit(1)
                
            # 6. Verify WAC Recalculation at Destination
            # Expected Dest WAC: (20*15 + 40*10) / 60 = 700 / 60 = 11.6666...
            expected_wac = Decimal("11.6667") # rounded to 4 decimals
            if abs(val_dest_final.weighted_average_cost - expected_wac) < Decimal("0.0001"):
                 print(f"   [PASS] Destination WAC correctly recalculated: {val_dest_final.weighted_average_cost}")
            else:
                 print(f"   [FAIL] WAC mismatch! Expected {expected_wac}, got {val_dest_final.weighted_average_cost}")
                 sys.exit(1)

            # 7. Idempotency Check
            print("\n   [STEP 3] Testing Idempotency (Duplicate Receive)...")
            await transfer_svc.receive_transfer(
                wh_src, wh_dest, product_id, Decimal("40.0"), uom_id, Decimal("4.0"),
                company_dest, transfer_id
            )
            await db.commit()
            
            val_dest_idemp = await repo.get_wac_valuation(product_id, wh_dest, company_dest)
            if val_dest_idemp.total_units == Decimal("60.0"):
                print("   [PASS] Idempotency guard blocked duplicate valuation.")
            else:
                print(f"   [FAIL] Idempotency failed! Total units: {val_dest_idemp.total_units}")
                sys.exit(1)

        except Exception:
            print("\n[CRITICAL ERROR] SCRIPT EXECUTION:")
            traceback.print_exc()
            sys.exit(1)
            
    await engine.dispose()
    print("\n--- Financial Regression Test Completed Successfully ---")

if __name__ == "__main__":
    asyncio.run(test_financial_regression())
