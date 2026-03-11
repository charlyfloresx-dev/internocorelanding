import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.domain.repositories.inventory_repository import IInventoryRepository
from app.dependencies.repositories import get_inventory_repository
from app.core.workers.reconciliation_worker import ReconciliationWorker
from common.responses import ApiResponse
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload

router = APIRouter()

@router.post("/reconcile/{error_id}", response_model=ApiResponse)
async def manual_reconcile(
    error_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    repository: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    On-Demand Reconciliation: Manually triggers the backflushing logic for a specific error.
    Used by warehouse managers after replenishing stock or fixings BOMs.
    """
    # 1. Fetch error record
    from app.models.backflush_error import BackflushStatus
    
    record = await repository.get_backflush_error(error_id, token.company_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Backflush error record not found.")
    
    if record["status"] == getattr(BackflushStatus.RESOLVED, "value", str(BackflushStatus.RESOLVED)) or record["status"] == "RESOLVED":
        return ApiResponse(status="success", message="This record is already resolved.")

    # 2. Trigger individual reconciliation logic
    # (Reusing worker's internal logic)
    from app.events.consumers.production_consumer import ProductionReportedConsumer
    consumer = ProductionReportedConsumer(db)
    
    worker = ReconciliationWorker()
    success, details = await worker._attempt_reconciliation(consumer, record)
    
    # 3. Update DB
    await repository.update_reconciliation_status(
        error_id=error_id,
        success=success,
        details=details
    )
    
    await db.commit()
    
    if success:
        return ApiResponse(status="success", message="Manual reconciliation successful.")
    else:
        raise HTTPException(status_code=400, detail=f"Reconciliation still failing: {details}")
