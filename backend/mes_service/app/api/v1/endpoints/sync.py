import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Decimal
from app.dependencies import get_db
from app.services.scanner_service import ScannerService
from common.responses import ApiResponse

router = APIRouter()

class SyncEntry(BaseModel):
    local_txn_id: uuid.UUID
    resource_result_id: uuid.UUID
    sku: str
    qty: float
    sequence_number: int
    created_at: datetime
    external_folio: Optional[str] = None

class SyncRequest(BaseModel):
    entries: List[SyncEntry]

@router.post("/sync")
async def sync_production(
    request: SyncRequest,
    company_id: uuid.UUID = Query(...), # En prod vendría del JWT
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza un lote de transacciones desde el Edge.
    Aplica protección multi-tenant y de-duplicación por local_txn_id.
    """
    service = ScannerService(db)
    synced_count, skipped_count = await service.process_sync_batch(request.entries, company_id)
    
    return {
        "status": "success",
        "message": f"Sync completed: {synced_count} processed, {skipped_count} skipped.",
        "meta": {
            "synced": synced_count,
            "skipped": skipped_count
        }
    }
