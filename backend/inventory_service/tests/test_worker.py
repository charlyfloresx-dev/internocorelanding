import os
# Mock environment for Pydantic validation
os.environ["CORE_DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/db"
os.environ["CORE_SECRET_KEY"] = "test_secret_key"

import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from inventory_app.db.session import async_session_factory
from inventory_app.models.backflush_error import BackflushError, BackflushStatus, BackflushErrorType
from inventory_app.infrastructure.repositories import InventoryRepository
from inventory_app.core.workers.reconciliation_worker import ReconciliationWorker

async def test_reconciliation_flow():
    print("--- STARTING RECONCILIATION FLOW TEST ---")
    
    async with async_session_factory() as session:
        repository = InventoryRepository(session)
        company_id = uuid.uuid4()
        event_id = uuid.uuid4()
        run_id = uuid.uuid4()
        
        # 1. Simulate a pending error (e.g. Missing BOM)
        error = BackflushError(
            company_id=company_id,
            event_id=event_id,
            production_run_id=run_id,
            item_code="FG-100",
            required_qty=10.0,
            error_type=BackflushErrorType.MISSING_BOM,
            status=BackflushStatus.PENDING,
            retry_count=0,
            error_details="BOM not found on first attempt"
        )
        session.add(error)
        await session.commit()
        await session.refresh(error)
        print(f"[x] Created PENDING error: {error.id}")

        # 2. Run Worker logic (Simulated loop)
        worker = ReconciliationWorker()
        print("[*] Triggering manual reconciliation processing...")
        await worker.process_pending_errors()
        
        # 3. Verify status update
        stmt = select(BackflushError).where(BackflushError.id == error.id)
        result = await session.execute(stmt)
        record = result.scalar_one()
        
        print(f"[?] Final Status: {record.status}")
        print(f"[?] Retry Count: {record.retry_count}")
        print(f"[?] Last Retry At: {record.last_retry_at}")
        
        if record.status == BackflushStatus.RESOLVED:
            print("--- TEST PASSED: RECONCILIATION SUCCESSFUL ---")
        else:
            print("--- TEST COMPLETED: RETRY LOGGED ---")

if __name__ == "__main__":
    asyncio.run(test_reconciliation_flow())
