import sys
import os
import uuid
import asyncio
import traceback
from sqlalchemy import select

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
backend_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.append(project_root)
sys.path.append(backend_root)

from common.models import Base
from common.exceptions import UnauthorizedException
from app.db.session import AsyncSessionLocal, engine
from app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.models.warehouse import Warehouse

async def test_zero_trust():
    print("--- Starting Zero Trust Warehouse Test ---")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    company_a = uuid.uuid4()
    company_b = uuid.uuid4()
    
    warehouse_a = uuid.uuid4()
    
    async with AsyncSessionLocal() as db:
        repo = SQLAlchemyInventoryRepository(db)
        
        try:
            # 1. Setup: Create warehouse for Company A
            print(f"   Setting up Warehouse {warehouse_a} for Company A...")
            db.add(Warehouse(id=warehouse_a, code="WH-A", name="Warehouse A", company_id=company_a))
            await db.commit()
            
            # 2. Test: Company A access Warehouse A (Should PASS)
            print("   Testing authorized access (Company A -> Warehouse A)...")
            await repo._validate_warehouse_ownership(warehouse_a, company_a)
            print("   [PASS] Authorized access successful.")
            
            # 3. Test: Company B access Warehouse A (Should FAIL)
            print("   Testing unauthorized access (Company B -> Warehouse A)...")
            try:
                await repo._validate_warehouse_ownership(warehouse_a, company_b)
                print("   [FAIL] Unauthorized access was NOT blocked!")
                sys.exit(1)
            except UnauthorizedException as e:
                print(f"   [PASS] Access blocked as expected: {e.message}")
                
            # 4. Verify Audit Log
            print("   Verifying Audit Log entry...")
            from common.models.audit_log import AuditLog
            stmt = select(AuditLog).filter_by(action="UNAUTHORIZED_WAREHOUSE_ACCESS", record_id=str(warehouse_a))
            result = await db.execute(stmt)
            log = result.scalar_one_or_none()
            
            if log:
                print(f"   [PASS] Audit log found: Action={log.action}, Company_ID={log.new_value.get('denied_to_company')}")
            else:
                print("   [FAIL] Audit log entry NOT found!")
                sys.exit(1)
                
        except Exception:
            print("\n[CRITICAL ERROR] SCRIPT EXECUTION:")
            traceback.print_exc()
            sys.exit(1)
            
    await engine.dispose()
    print("\n--- Zero Trust Warehouse Test Completed Successfully ---")

if __name__ == "__main__":
    asyncio.run(test_zero_trust())
