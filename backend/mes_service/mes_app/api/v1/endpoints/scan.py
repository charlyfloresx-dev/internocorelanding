from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.dependencies import (
    get_production_run_repo, get_ledger_repo, get_labor_repo,
    get_wms_client, get_current_company, get_work_order_repo,
)
from mes_app.domain.repositories.interfaces import (
    IProductionRunRepository, IManufacturingLedgerRepository,
    ILaborRepository, IWMSClient, IWorkOrderRepository,
)
from mes_app.services.scanner_service import ScannerService
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from typing import Optional

from common.responses import ApiResponse
from common.security.dependencies import require_scope

router = APIRouter()


class ScanRequest(BaseModel):
    resource_result_id: uuid.UUID = Field(description="Target Resource Result/Shift ID")
    scan_input: str = Field(description="Raw scan data from barcode/reader")
    local_txn_id: Optional[uuid.UUID] = Field(None, description="Idempotency local ID from Edge")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


@router.post("/scan", dependencies=[Depends(require_scope(["mes:write"]))])
async def process_scan(
    request: ScanRequest,
    company_id: uuid.UUID = Depends(get_current_company),
    run_repo: IProductionRunRepository = Depends(get_production_run_repo),
    ledger_repo: IManufacturingLedgerRepository = Depends(get_ledger_repo),
    labor_repo: ILaborRepository = Depends(get_labor_repo),
    wms_client: IWMSClient = Depends(get_wms_client),
    wo_repo: IWorkOrderRepository = Depends(get_work_order_repo),
):
    """
    Procesa un escaneo de producción. Los errores de negocio lanzan BusinessRuleException
    capturada por el domain_exception_handler.
    """
    service = ScannerService(run_repo, ledger_repo, labor_repo, wms_client, wo_repo)
    ledger_entry, warning = await service.process_scan(
        resource_result_id=request.resource_result_id,
        scan_input=request.scan_input,
        company_id=company_id,
        local_txn_id=request.local_txn_id,
    )

    return {
        "id": ledger_entry.id,
        "sku": ledger_entry.sku,
        "qty": str(Decimal(ledger_entry.qty)),
        "sequence_number": ledger_entry.sequence_number,
        "warning": warning,
    }
