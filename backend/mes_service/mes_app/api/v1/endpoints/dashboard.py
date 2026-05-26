from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.dependencies import (
    get_production_run_repo, get_ledger_repo, 
    get_downtime_repo, get_labor_repo, get_goal_repo
)
from mes_app.domain.repositories.interfaces import (
    IProductionRunRepository, IManufacturingLedgerRepository,
    IDowntimeRepository, ILaborRepository, IGoalRepository
)
from mes_app.services.kpi_service import KPIService
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from typing import List, Dict, Any

from common.responses import ApiResponse
from common.security.dependencies import require_scope

router = APIRouter()

# Schemas
class MetricSummary(BaseModel):
    produced: float = Field(description="Total units produced in the shift")
    downtime_minutes: float = Field(description="Total minutes in downtime")
    labor_minutes: float = Field(description="Total cumulative labor minutes")
    shift_duration_minutes: float = Field(description="Total elapsed minutes of the shift")

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class OeeResponse(BaseModel):
    oee: float = Field(description="Overall Equipment Effectiveness percentage")
    availability: float = Field(description="Availability percentage (Uptime vs Planned)")
    performance: float = Field(description="Performance percentage (Efficiency pieces vs rate)")
    quality: float = Field(description="Quality percentage")
    adjusted_meta: int = Field(description="Dynamic production goal adjusted by labor")
    andon_status: str = Field(description="Current status: OPERATING, DOWNTIME_PENDING, REPAIRING")
    metrics: MetricSummary

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class TrendGraphic(BaseModel):
    categories: List[str]
    meta: List[int]
    real: List[float]
    efficiency: List[float]
    accumulated_real: List[float]
    accumulated_meta: List[int]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class ParetoEntry(BaseModel):
    reason: str
    minutes: float

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

# Endpoints
@router.get("/oee/{resource_result_id}", response_model=OeeResponse, dependencies=[Depends(require_scope(["mes:read"]))])
async def get_oee(
    resource_result_id: uuid.UUID, 
    run_repo: IProductionRunRepository = Depends(get_production_run_repo),
    ledger_repo: IManufacturingLedgerRepository = Depends(get_ledger_repo),
    downtime_repo: IDowntimeRepository = Depends(get_downtime_repo),
    labor_repo: ILaborRepository = Depends(get_labor_repo),
    goal_repo: IGoalRepository = Depends(get_goal_repo)
):
    """
    Retorna OEE consolidado con estado Andon.
    """
    service = KPIService(run_repo, ledger_repo, downtime_repo, labor_repo, goal_repo)
    return await service.calculate_oee(resource_result_id)

@router.get("/graphic/{resource_result_id}", response_model=TrendGraphic, dependencies=[Depends(require_scope(["mes:read"]))])
async def get_graphic(
    resource_result_id: uuid.UUID, 
    run_repo: IProductionRunRepository = Depends(get_production_run_repo),
    ledger_repo: IManufacturingLedgerRepository = Depends(get_ledger_repo),
    downtime_repo: IDowntimeRepository = Depends(get_downtime_repo),
    labor_repo: ILaborRepository = Depends(get_labor_repo),
    goal_repo: IGoalRepository = Depends(get_goal_repo)
):
    """
    Retorna gráfico de tendencias (Meta vs Real).
    """
    service = KPIService(run_repo, ledger_repo, downtime_repo, labor_repo, goal_repo)
    return await service.get_resource_graphic(resource_result_id)

@router.get("/pareto/{resource_result_id}", response_model=List[ParetoEntry], dependencies=[Depends(require_scope(["mes:read"]))])
async def get_pareto(
    resource_result_id: uuid.UUID, 
    run_repo: IProductionRunRepository = Depends(get_production_run_repo),
    ledger_repo: IManufacturingLedgerRepository = Depends(get_ledger_repo),
    downtime_repo: IDowntimeRepository = Depends(get_downtime_repo),
    labor_repo: ILaborRepository = Depends(get_labor_repo),
    goal_repo: IGoalRepository = Depends(get_goal_repo)
):
    """
    Retorna Pareto de las top causas de paro.
    """
    service = KPIService(run_repo, ledger_repo, downtime_repo, labor_repo, goal_repo)
    # Note: Pareto analysis logic was using complex SQL inside service. 
    # For MVP compliance, we'll keep it as is or move to repo.
    # Refactoring KPIService to use higher level methods anyway.
    return await service.get_pareto_analysis(resource_result_id)
