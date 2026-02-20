from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.services.scanner_service import ScannerService
from pydantic import BaseModel
import uuid
from typing import Optional

from common.responses import ApiResponse

router = APIRouter()

class ScanRequest(BaseModel):
    resource_result_id: uuid.UUID
    scan_input: str
    local_txn_id: Optional[uuid.UUID] = None
    company_id: uuid.UUID

@router.post("/scan")
async def process_scan(request: ScanRequest, db: AsyncSession = Depends(get_db)):
    """
    Procesa un escaneo. Los errores de negocio lanzan BusinessRuleException
    que es capturada por el domain_exception_handler.
    """
    service = ScannerService(db)
    ledger_entry, warning = await service.process_scan(
        resource_result_id=request.resource_result_id,
        scan_input=request.scan_input,
        company_id=request.company_id,
        local_txn_id=request.local_txn_id
    )
    
    return {
        "id": ledger_entry.id,
        "sku": ledger_entry.sku,
        "qty": float(ledger_entry.qty),
        "sequence_number": ledger_entry.sequence_number,
        "warning": warning
    }
