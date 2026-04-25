"""
API Endpoints — Opportunities Router

Rutas del CRM Kanban:
  POST  /evaluate          → Recibe payload de full-report, evalúa y persiste.
  GET   /                  → Lista oportunidades con filtros (ROI, status, needs_data).
  GET   /{cve_cat}         → Detalle de una oportunidad específica.
  PATCH /{cve_cat}/status  → Mueve el predio en el Kanban.
  PATCH /{cve_cat}/data    → Completa datos faltantes (when needs_manual_data=True).
  GET   /zones             → Lista colonias con VM configurado.
"""
from typing import Any, List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status as http_status

from sqlalchemy.ext.asyncio import AsyncSession

from asset_app.core.database import get_db
from asset_app.application.schemas.opportunity import (
    FullReportInput,
    OpportunityResponse,
    OpportunityStatusUpdate,
    OpportunityManualUpdate,
    ZoneConfigCreate,
    ZoneConfigResponse,
)
from asset_app.application.services.opportunity_orchestrator import OpportunityOrchestrator
from asset_app.infrastructure.repositories.opportunity_repository import OpportunityRepository
from asset_app.domain.exceptions import OpportunityNotFoundException
from common.security.dependencies import get_current_user
from common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ─── POST /evaluate ───────────────────────────────────────────────────────────

@router.post(
    "/evaluate",
    response_model=OpportunityResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Evalúa y registra un predio como Oportunidad de Inversión",
)
async def evaluate_opportunity(
    payload: FullReportInput,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """
    Recibe los datos del /full-report del GIS y los procesa financieramente.
    Puede llamarse directamente desde el frontend o vía BackgroundTask interna.
    """
    payload.created_by = current_user.get("user_id")
    orchestrator = OpportunityOrchestrator(db)
    try:
        opp = await orchestrator.process_full_report(payload)
        return _to_response(opp)
    except Exception as e:
        logger.error(f"[/evaluate] Error procesando {payload.cve_cat}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── GET / ────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[OpportunityResponse],
    summary="Lista predios evaluados, ordenados por mayor ROI",
)
async def list_opportunities(
    status: Optional[str] = Query(None, description="Filtrar por etapa Kanban (ej. Scouting)"),
    needs_data: Optional[bool] = Query(None, alias="needs_data", description="Solo predios con datos incompletos"),
    min_roi: Optional[Decimal] = Query(None, description="ROI mínimo en MXN"),
    opportunities_only: bool = Query(False, description="Solo predios marcados como is_investment_opportunity"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> Any:
    repo = OpportunityRepository(db)
    results = await repo.list_opportunities(
        status=status,
        needs_manual_data=needs_data,
        min_roi=min_roi,
        is_opportunity_only=opportunities_only,
        limit=limit,
        offset=offset,
    )
    return [_to_response(o) for o in results]


# ─── GET /{cve_cat} ──────────────────────────────────────────────────────────

@router.get(
    "/{cve_cat}",
    response_model=OpportunityResponse,
    summary="Detalle completo de un predio específico",
)
async def get_opportunity(
    cve_cat: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> Any:
    repo = OpportunityRepository(db)
    opp = await repo.get_by_cve_cat(cve_cat)
    if not opp:
        raise HTTPException(status_code=404, detail=f"No se encontró el predio: {cve_cat}")
    return _to_response(opp)


# ─── PATCH /{cve_cat}/status ─────────────────────────────────────────────────

@router.patch(
    "/{cve_cat}/status",
    response_model=OpportunityResponse,
    summary="Mueve el predio en el Pipeline Kanban",
)
async def update_opportunity_status(
    cve_cat: str,
    payload: OpportunityStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Any:
    repo = OpportunityRepository(db)
    opp = await repo.update_status(
        cve_cat=cve_cat,
        new_status=payload.status,
        performed_by=current_user.get("user_id"),
        notes=payload.notes,
    )
    if not opp:
        raise HTTPException(status_code=404, detail=f"No se encontró el predio: {cve_cat}")
    return _to_response(opp)


# ─── PATCH /{cve_cat}/data ───────────────────────────────────────────────────

@router.patch(
    "/{cve_cat}/data",
    response_model=OpportunityResponse,
    summary="Completa datos faltantes manualmente (needs_manual_data=True)",
)
async def update_opportunity_data(
    cve_cat: str,
    payload: OpportunityManualUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> Any:
    """
    Permite que Indiana o el operador ingresen datos que el sistema no pudo obtener
    automáticamente (ej. valor_m2_zona cuando la colonia no está en ZoneConfig).
    El sistema recalcula el ROI automáticamente si hay suficientes datos.
    """
    repo = OpportunityRepository(db)
    updates = payload.model_dump(exclude_none=True)
    opp = await repo.apply_manual_update(cve_cat=cve_cat, updates=updates)
    if not opp:
        raise HTTPException(status_code=404, detail=f"No se encontró el predio: {cve_cat}")
    return _to_response(opp)


# ─── GET /zones ──────────────────────────────────────────────────────────────

@router.get(
    "/zones/config",
    response_model=List[ZoneConfigResponse],
    summary="Lista colonias con Valor de Mercado configurado",
)
async def list_zone_configs(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
) -> Any:
    repo = OpportunityRepository(db)
    zones = await repo.list_zone_configs()
    return zones


# ─── Helper ──────────────────────────────────────────────────────────────────

def _to_response(opp) -> OpportunityResponse:
    """Convierte un modelo SQLAlchemy a un schema Pydantic con el campo calculado days_in_pipeline."""
    data = {
        c.name: getattr(opp, c.name)
        for c in opp.__table__.columns
    }
    data["days_in_pipeline"] = opp.days_in_pipeline
    return OpportunityResponse(**data)
