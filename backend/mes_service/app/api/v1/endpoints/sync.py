import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from app.dependencies import get_db, get_current_company
from app.services.scanner_service import ScannerService
from common.responses import ApiResponse

router = APIRouter()

class SyncEntry(BaseModel):
    local_txn_id: uuid.UUID = Field(description="Original local transaction ID")
    resource_result_id: uuid.UUID = Field(description="Target shift result ID")
    sku: str = Field(description="Product SKU")
    qty: float = Field(description="Quantity produced")
    sequence_number: int = Field(description="Local sequence number")
    created_at: datetime = Field(description="Original creation timestamp at Edge")
    external_folio: Optional[str] = Field(None, description="Optional WO/Folio reference")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class SyncRequest(BaseModel):
    entries: List[SyncEntry]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

@router.post("/sync")
async def sync_production(
    request: SyncRequest,
    company_id: uuid.UUID = Depends(get_current_company),
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
