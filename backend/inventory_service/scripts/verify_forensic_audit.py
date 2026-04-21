import sys
import os
import uuid
import asyncio
import traceback
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Add the project root to sys.path to allow absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
backend_root = os.path.abspath(os.path.join(current_dir, '../..'))

sys.path.append(project_root)
sys.path.append(backend_root)

# Force load models to register them with Base.metadata
from inventory_app.models.movement import Movement
from common.models.audit_log import AuditLog
from common.models import Base

from inventory_app.db.session import AsyncSessionLocal, engine
from inventory_app.services.inventory import InventoryTransactionService
from inventory_app.schemas.inventory import InventoryTransactionCreate
from inventory_app.models.inventory import TransactionType
from common.context import request_context
from common.domain.entities.user_context import UserContext
from sqlalchemy import select
from inventory_app.core.events import setup_audit_listeners, ForensicImmutabilityError

async def verify_forensic_audit():
    print("--- Starting Forensic Verification Plan ---")
    
    # 0. Setup: Ensure tables exist and listeners are registered
    print("   Setting up database tables and listeners...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        setup_audit_listeners()
    except Exception as e:
        print(f"   [FAIL] Setup Error: {e}")
        return

    company_id = uuid.uuid4()
    user_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    # Setup context
    ctx = UserContext(
        user_id=user_id,
        company_id=company_id,
        trace_id=trace_id
    )
    request_context.set(ctx)

    async with AsyncSessionLocal() as db:
        try:
            # TEST 1: Immutability (Update/Delete blocking)
            print("\n1. Testing Immutability...")
            movement = Movement(
                id=uuid.uuid4(),
                warehouse_id=uuid.uuid4(),
                product_id=uuid.uuid4(),
                company_id=company_id,
                quantity=Decimal("10.0"),
                uom_id=uuid.uuid4(),
                weight=Decimal("10.0"),
                unit_price=Decimal("1.0"),
                movement_type="IN",
                document_type="TEST",
                document_id=uuid.uuid4()
            )
            db.add(movement)
            await db.commit()
            print(f"   Created movement: {movement.id}")

            # Attempt UPDATE
            try:
                # Refresh object
                result = await db.execute(select(Movement).filter(Movement.id == movement.id))
                mov_to_update = result.scalar_one()
                mov_to_update.quantity = Decimal("20.0")
                await db.commit()
                print("   [FAIL] Update should have been blocked")
            except ForensicImmutabilityError as e:
                print(f"   [PASS] Update blocked as expected. ({e})")
                await db.rollback()
            except Exception as e:
                print(f"   [FAIL] Unexpected error during update: {type(e).__name__}: {e}")
                await db.rollback()

            # Attempt DELETE
            try:
                result = await db.execute(select(Movement).filter(Movement.id == movement.id))
                mov_to_delete = result.scalar_one()
                await db.delete(mov_to_delete)
                await db.commit()
                print("   [FAIL] Delete should have been blocked")
            except ForensicImmutabilityError as e:
                print(f"   [PASS] Delete blocked as expected. ({e})")
                await db.rollback()
            except Exception as e:
                print(f"   [FAIL] Unexpected error during delete: {type(e).__name__}: {e}")
                await db.rollback()

            # TEST 2: Warehouse Guard (Cyclic Transfers)
            print("\n2. Testing Warehouse Guard (Cyclic Transfers)...")
            w_id = uuid.uuid4()
            stmt = InventoryTransactionCreate(
                product_id=uuid.uuid4(),
                warehouse_id=w_id,
                target_warehouse_id=w_id, # SAME
                quantity_change=Decimal("5.0"),
                transaction_type=TransactionType.TRANSFER,
                uom_id=uuid.uuid4(),
                weight=Decimal("5.0")
            )
            try:
                await InventoryTransactionService.create_transaction(
                    db, stmt, company_id, user_id, uuid.UUID(trace_id), "token"
                )
                print("   [FAIL] Cyclic transfer should have been rejected")
            except ValueError as e:
                if "ERR_CYCLIC_TRANSFER" in str(e):
                    print(f"   [PASS] Cyclic transfer rejected.")
                else:
                    print(f"   [FAIL] Unexpected error message: {e}")
            except Exception as e:
                 print(f"   [FAIL] Unexpected exception type: {type(e).__name__}: {e}")

            # TEST 3: Traceability (X-Trace-ID in audit logs)
            print("\n3. Testing Traceability (Correlation-ID)...")
            with patch('app.services.inventory.MasterDataClient') as mock_md_client_class:
                mock_md_instance = mock_md_client_class.return_value
                async def mock_get_factor(*args, **kwargs): return Decimal("1.0")
                async def mock_validate(*args, **kwargs): return True
                mock_md_instance.get_uom_factor = mock_get_factor
                mock_md_instance.validate_product = mock_validate
                
                p_id = uuid.uuid4()
                stmt_tr = InventoryTransactionCreate(
                    product_id=p_id,
                    warehouse_id=uuid.uuid4(),
                    quantity_change=Decimal("10.0"),
                    transaction_type=TransactionType.IN,
                    uom_id=uuid.uuid4(),
                    weight=Decimal("10.0")
                )
                
                # New context for this transaction
                new_trace_id = str(uuid.uuid4())
                request_context.get().trace_id = new_trace_id
                
                movement_new = await InventoryTransactionService.create_transaction(
                    db, stmt_tr, company_id, user_id, uuid.UUID(new_trace_id), "token"
                )
                await db.commit() # Ensure the after_insert listener runs and commits
                
                # Check audit_logs
                result = await db.execute(
                    select(AuditLog).where(AuditLog.record_id == str(movement_new.id)).order_by(AuditLog.timestamp.desc())
                )
                audit = result.scalars().first()
                if audit and audit.trace_id == new_trace_id:
                    print(f"   [PASS] Audit log captured trace_id: {audit.trace_id}")
                else:
                    print(f"   [FAIL] Trace ID mismatch in audit log. Found: {audit.trace_id if audit else 'None'}")

            # TEST 4: Weight Discrepancy Test (Edge Case)
            print("\n4. Testing Weight Discrepancy...")
            with patch('app.services.inventory.MasterDataClient') as mock_md_client_class:
                mock_md_instance = mock_md_client_class.return_value
                async def mock_get_factor_2(*args, **kwargs): return Decimal("2.0")
                mock_md_instance.get_uom_factor = mock_get_factor_2
                
                stmt_wt = InventoryTransactionCreate(
                    product_id=uuid.uuid4(),
                    warehouse_id=uuid.uuid4(),
                    quantity_change=Decimal("10.0"),
                    transaction_type=TransactionType.IN,
                    uom_id=uuid.uuid4(),
                    weight=Decimal("19.0") # Should be 20.0
                )
                try:
                    await InventoryTransactionService.create_transaction(
                        db, stmt_wt, company_id, user_id, uuid.UUID(trace_id), "token"
                    )
                    print("   [FAIL] Weight discrepancy should have been caught")
                except ValueError as e:
                    if "ERR_WEIGHT_MISMATCH" in str(e):
                        print(f"   [PASS] Weight mismatch detected.")
                    else:
                        print(f"   [FAIL] Unexpected error message: {e}")

            # TEST 5: Multitenancy Cross-Pollination (Edge Case)
            print("\n5. Testing Multitenancy Cross-Pollination...")
            with patch('app.services.inventory.MasterDataClient') as mock_md_client_class:
                mock_md_instance = mock_md_client_class.return_value
                async def mock_validate_false(*args, **kwargs): return False
                mock_md_instance.validate_product = mock_validate_false
                
                stmt_mt = InventoryTransactionCreate(
                    product_id=uuid.uuid4(),
                    warehouse_id=uuid.uuid4(),
                    quantity_change=Decimal("10.0"),
                    transaction_type=TransactionType.IN,
                    uom_id=uuid.uuid4(),
                    weight=Decimal("10.0")
                )
                try:
                     await InventoryTransactionService.create_transaction(
                         db, stmt_mt, company_id, user_id, uuid.UUID(trace_id), "token"
                     )
                     print("   [FAIL] Cross-pollination should have been caught by product validation")
                except ValueError as e:
                     if "ERR_INVALID_PRODUCT" in str(e):
                         print("   [PASS] Cross-pollination blocked via product ownership validation.")
                     else:
                         print(f"   [FAIL] Unexpected error message: {e}")

        except Exception:
            print("\n[CRITICAL ERROR] SCRIPT EXECUTION:")
            traceback.print_exc()

    await engine.dispose()
    print("\n--- Forensic Verification Completed ---")

if __name__ == "__main__":
    asyncio.run(verify_forensic_audit())
