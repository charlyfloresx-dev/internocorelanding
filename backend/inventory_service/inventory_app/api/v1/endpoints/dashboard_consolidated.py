import uuid
from typing import List
from fastapi import APIRouter, Depends, Header, Request, Response
from inventory_app.infrastructure.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from inventory_app.dependencies.repositories import get_inventory_repository
from inventory_app.infrastructure.clients.master_data import MasterDataClient
from inventory_app.api.v1.handlers.dashboard_handler import GetInventoryDashboardHandler
from inventory_app.schemas.dashboard import DashboardDTO
from common.responses import ApiResponse

router = APIRouter()

@router.get("/mission-control", response_model=ApiResponse[DashboardDTO])
async def get_dashboard_mission_control(
    warehouse_id: uuid.UUID,
    repo: SQLAlchemyInventoryRepository = Depends(get_inventory_repository),
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
    md_client = MasterDataClient()
    handler = GetInventoryDashboardHandler(repo, md_client)
    
    dashboard_data = await handler.execute(
        warehouse_id=warehouse_id,
        company_id=x_company_id,
        trace_id=trace_id
    )
    
    # We return the model directly and let FastAPI's response_model and 
    # jsonable_encoder handle the heavy lifting. The middleware will process it.
    return ApiResponse(status="success", data=dashboard_data)

@router.get("/consolidated", response_model=ApiResponse[List[DashboardDTO]])
async def get_dashboard_mission_control_consolidated(
    repo: SQLAlchemyInventoryRepository = Depends(get_inventory_repository),
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

    md_client = MasterDataClient()
    handler = GetInventoryDashboardHandler(repo, md_client)
    
    consolidated_data = await handler.execute_consolidated(
        company_id=x_company_id,
        trace_id=trace_id
    )
    
    return ApiResponse(status="success", data=consolidated_data)
