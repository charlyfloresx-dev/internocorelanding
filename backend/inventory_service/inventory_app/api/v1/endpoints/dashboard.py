import uuid
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.dependencies.repositories import get_inventory_repository
from inventory_app.schemas.dashboard import (
    StockDashboardRow, ForceReleaseCmd, InventorySummary, MovementDocumentRow,
    KardexRow, WACValuationRow, ABCRotationRow, DashboardDTO
)
from common.responses import ApiResponse
from common.security.auth_payload import TokenPayload

router = APIRouter()

def require_owner_role(request: Request):
    """Dependency to enforce OWNER or ADMIN role for emergency actions."""
    token_data: TokenPayload = getattr(request.state, "user_token", None)
    if not token_data or token_data.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Access Denied: Requires OWNER or ADMIN role.")
    return token_data

@router.get("/summary", response_model=ApiResponse[InventorySummary])
async def get_inventory_summary(
    request: Request,
    warehouse_id: Optional[uuid.UUID] = None,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: Union[uuid.UUID, str] = Header(...)
):
    """
    Returns aggregated counts for the top dashboard cards.
    """
    summary = await repo.get_inventory_summary(x_company_id, warehouse_id)
    return ApiResponse(data=summary)

@router.get("/movements", response_model=ApiResponse[List[MovementDocumentRow]])
async def list_movements(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    type: Optional[str] = None,
    warehouse_id: Optional[uuid.UUID] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: Union[uuid.UUID, str] = Header(...)
):
    """
    Returns a paginated & filtered list of inventory documents.
    Supports optional date range: date_from / date_to (ISO 8601).
    """
    movements, total = await repo.list_movements(
        company_id=x_company_id,
        limit=limit,
        offset=offset,
        movement_type=type,
        warehouse_id=warehouse_id,
        date_from=date_from,
        date_to=date_to
    )
    return ApiResponse(data=movements, meta={"total_records": total})

@router.get("/stock", response_model=ApiResponse[List[StockDashboardRow]])
async def get_dashboard_stock(
    request: Request,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: Union[uuid.UUID, str] = Header(...)
):
    """
    Returns the consolidated view of physical and transit stock.
    Accessible by all valid tenant users.
    """
    rows = await repo.get_dashboard_stock(x_company_id)
    return ApiResponse(data=rows)

@router.post("/force-release", response_model=ApiResponse, dependencies=[Depends(require_owner_role)])
async def force_release_reservation(
    cmd: ForceReleaseCmd,
    request: Request,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: Union[uuid.UUID, str] = Header(...)
):
    """
    [EMERGENCY] Releases stuck reserved_quantity.
    Requires OWNER/ADMIN role.
    """
    try:
        stock = await repo.force_release_orphan(
            warehouse_id=cmd.warehouse_id,
            product_id=cmd.product_id,
            release_qty=cmd.release_qty,
            company_id=x_company_id
        )
        return ApiResponse(
            message="Reservation forcibly released", 
            data={"available_quantity": stock.available_quantity, "reserved_quantity": stock.reserved_quantity}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── REPORT ENDPOINTS ─────────────────────────────────────────────────────────────

@router.get("/reports/kardex", response_model=ApiResponse[List[KardexRow]])
async def get_kardex_report(
    product_id: Union[uuid.UUID, str],
    warehouse_id: Union[uuid.UUID, str],
    limit: int = 200,
    request: Request = None,
    response: Response = None,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: Union[uuid.UUID, str] = Header(...)
):
    """
    Kardex: Running balance for a specific SKU/Warehouse.
    Uses SQL Window Function SUM OVER (ORDER BY created_at).
    """
    trace_id = (request.headers.get("x-correlation-id") or str(uuid.uuid4())) if request else str(uuid.uuid4())
    if response:
        response.headers["X-Trace-ID"] = trace_id

    rows = await repo.get_kardex(
        product_id=product_id,
        warehouse_id=warehouse_id,
        company_id=x_company_id,
        limit=limit
    )
    return ApiResponse(data=rows, meta={"count": len(rows), "product_id": str(product_id), "trace_id": trace_id})

@router.get("/reports/valuation", response_model=ApiResponse[WACValuationRow])
async def get_wac_valuation_report(
    product_id: Union[uuid.UUID, str],
    warehouse_id: Union[uuid.UUID, str],
    as_of_date: Optional[str] = None,
    request: Request = None,
    response: Response = None,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: Union[uuid.UUID, str] = Header(...)
):
    """
    WAC Valuation: Weighted Average Cost snapshot from the immutable Movement ledger.
    as_of_date: optional ISO 8601 cutoff for historical valuation.
    """
    trace_id = (request.headers.get("x-correlation-id") or str(uuid.uuid4())) if request else str(uuid.uuid4())
    if response:
        response.headers["X-Trace-ID"] = trace_id

    result = await repo.get_wac_valuation(
        product_id=product_id,
        warehouse_id=warehouse_id,
        company_id=x_company_id,
        as_of_date=as_of_date
    )
    if not result:
        raise HTTPException(status_code=404, detail="No movements found for this product/warehouse.")
    
    # Map from domain entity (Money) to API Schema (Decimal) to avoid Pydantic validation errors
    mapped_data = WACValuationRow(
        product_id=result.product_id,
        total_units=result.total_units,
        weighted_average_cost=result.wac.amount,
        total_inventory_value=result.total_inventory_value.amount,
        currency_code=result.wac.currency
    )
    
    return ApiResponse(data=mapped_data, meta={"trace_id": trace_id})

@router.get("/reports/abc", response_model=ApiResponse[List[ABCRotationRow]])
async def get_abc_rotation_report(
    warehouse_id: Optional[Union[uuid.UUID, str]] = None,
    request: Request = None,
    response: Response = None,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: Union[uuid.UUID, str] = Header(...)
):
    """
    ABC Rotation: Classifies every SKU by 30-day exit velocity.
    - A: rotation_index >= 0.7  (fast-movers)
    - B: 0.3 <= index < 0.7
    - C: index < 0.3            (slow-movers / dead stock)
    """
    trace_id = (request.headers.get("x-correlation-id") or str(uuid.uuid4())) if request else str(uuid.uuid4())
    if response:
        response.headers["X-Trace-ID"] = trace_id

    rows = await repo.get_abc_rotation(
        company_id=x_company_id,
        warehouse_id=warehouse_id
    )
# ─── MISSION CONTROL ENDPOINTS ───────────────────────────────────────────────────

@router.get("/mission-control", response_model=ApiResponse[DashboardDTO])
async def get_dashboard_mission_control(
    warehouse_id: uuid.UUID,
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...),
    request: Request = None,
    response: Response = None
):
    """
    Consolidatado de métricas de inventario para el Dashboard de Mission Control.
    Integra telemetría de SQL y metadatos de Master Data.
    """
    trace_id = (request.headers.get("x-correlation-id") or 
                request.headers.get("x-trace-id") or 
                str(uuid.uuid4()))
    if response:
        response.headers["X-Trace-ID"] = trace_id

    # DI for Handler
    from inventory_app.infrastructure.clients.master_data import MasterDataClient
    from inventory_app.api.v1.handlers.dashboard_handler import GetInventoryDashboardHandler
    
    md_client = MasterDataClient()
    handler = GetInventoryDashboardHandler(repo, md_client)
    
    dashboard_data = await handler.execute(
        warehouse_id=warehouse_id,
        company_id=x_company_id,
        trace_id=trace_id
    )
    
    return ApiResponse(status="success", data=dashboard_data)

@router.get("/consolidated", response_model=ApiResponse[List[DashboardDTO]])
async def get_dashboard_mission_control_consolidated(
    repo: IInventoryRepository = Depends(get_inventory_repository),
    x_company_id: uuid.UUID = Header(...),
    request: Request = None,
    response: Response = None
):
    """
    Returns telemetry for ALL warehouses of the company in a single request.
    Optimizes frontend performance and reduces request storm.
    """
    trace_id = (request.headers.get("x-correlation-id") or 
                request.headers.get("x-trace-id") or 
                str(uuid.uuid4()))
    if response:
        response.headers["X-Trace-ID"] = trace_id

    from inventory_app.infrastructure.clients.master_data import MasterDataClient
    from inventory_app.api.v1.handlers.dashboard_handler import GetInventoryDashboardHandler
    
    md_client = MasterDataClient()
    handler = GetInventoryDashboardHandler(repo, md_client)
    
    consolidated_data = await handler.execute_consolidated(
        company_id=x_company_id,
        trace_id=trace_id
    )
    
    return ApiResponse(status="success", data=consolidated_data)
