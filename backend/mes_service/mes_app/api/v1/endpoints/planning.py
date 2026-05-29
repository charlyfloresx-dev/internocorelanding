from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date
import uuid

from pydantic import BaseModel, ConfigDict

from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from common.exceptions import NotFoundException
from mes_app.dependencies import get_current_company
from mes_app.models.production_run import ProductionRun
from mes_app.models.work_order import WorkOrder
from mes_app.models.resource import Resource
from mes_app.models.shift import Shift
from mes_app.schemas.planning import PlanningEntry, BulkLoadResponse

router = APIRouter()


# ── Read schemas ──────────────────────────────────────────────────────────────

class ProductionRunRead(BaseModel):
    id: uuid.UUID
    work_order_id: uuid.UUID
    resource_id: uuid.UUID
    shift_id: uuid.UUID
    date: date
    planned_quantity: int
    actual_quantity: int
    # denormalized for UI (resolved from joined models)
    order_number: Optional[str] = None
    item_code: Optional[str] = None
    resource_code: Optional[str] = None
    resource_name: Optional[str] = None
    shift_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PlanningRunCreate(BaseModel):
    work_order_id: uuid.UUID
    resource_id: uuid.UUID
    shift_id: uuid.UUID
    production_date: date
    planned_quantity: int


# ── GET /runs — list runs for a date ─────────────────────────────────────────

@router.get(
    "/runs",
    response_model=List[ProductionRunRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
    summary="Listar corridas de producción planificadas para una fecha",
)
async def list_runs(
    target_date: Optional[date] = None,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    run_date = target_date or date.today()
    result = await db.execute(
        select(ProductionRun, WorkOrder, Resource, Shift)
        .join(WorkOrder, ProductionRun.work_order_id == WorkOrder.id)
        .join(Resource, ProductionRun.resource_id == Resource.id)
        .outerjoin(Shift, ProductionRun.shift_id == Shift.id)
        .where(
            ProductionRun.company_id == company_id,
            ProductionRun.date == run_date,
        )
    )
    rows = result.all()
    return [
        ProductionRunRead(
            id=run.id,
            work_order_id=run.work_order_id,
            resource_id=run.resource_id,
            shift_id=run.shift_id,
            date=run.date,
            planned_quantity=run.planned_quantity,
            actual_quantity=run.actual_quantity,
            order_number=wo.order_number,
            item_code=wo.item_code,
            resource_code=res.code,
            resource_name=res.name,
            shift_name=shift.name if shift else None,
        )
        for run, wo, res, shift in rows
    ]


# ── POST /runs — create single run ────────────────────────────────────────────

@router.post(
    "/runs",
    response_model=ProductionRunRead,
    status_code=201,
    dependencies=[Depends(require_scope(["mes:write"]))],
    summary="Crear corrida de producción individual",
)
async def create_run(
    body: PlanningRunCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    wo_result = await db.execute(
        select(WorkOrder).where(WorkOrder.id == body.work_order_id,
                                WorkOrder.company_id == company_id)
    )
    wo = wo_result.scalar_one_or_none()
    if not wo:
        raise NotFoundException("WorkOrder not found")

    res_result = await db.execute(
        select(Resource).where(Resource.id == body.resource_id,
                               Resource.company_id == company_id)
    )
    res = res_result.scalar_one_or_none()
    if not res:
        raise NotFoundException("Resource not found")

    shift_result = await db.execute(
        select(Shift).where(Shift.id == body.shift_id, Shift.company_id == company_id)
    )
    shift = shift_result.scalar_one_or_none()

    # Conflict check
    conflict = (await db.execute(
        select(ProductionRun).where(
            ProductionRun.resource_id == body.resource_id,
            ProductionRun.shift_id == body.shift_id,
            ProductionRun.date == body.production_date,
            ProductionRun.company_id == company_id,
        )
    )).scalar_one_or_none()
    if conflict:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Resource already has a run on {body.production_date} for this shift"
        )

    run = ProductionRun(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        work_order_id=body.work_order_id,
        resource_id=body.resource_id,
        shift_id=body.shift_id,
        date=body.production_date,
        planned_quantity=body.planned_quantity,
        actual_quantity=0,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    return ProductionRunRead(
        id=run.id,
        work_order_id=run.work_order_id,
        resource_id=run.resource_id,
        shift_id=run.shift_id,
        date=run.date,
        planned_quantity=run.planned_quantity,
        actual_quantity=run.actual_quantity,
        order_number=wo.order_number,
        item_code=wo.item_code,
        resource_code=res.code,
        resource_name=res.name,
        shift_name=shift.name if shift else None,
    )


# ── DELETE /runs/{id} — cancel/remove a planned run ──────────────────────────

@router.delete(
    "/runs/{run_id}",
    status_code=204,
    dependencies=[Depends(require_scope(["mes:write"]))],
    summary="Eliminar corrida planificada",
)
async def delete_run(
    run_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductionRun).where(
            ProductionRun.id == run_id,
            ProductionRun.company_id == company_id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise NotFoundException("ProductionRun not found")
    await db.delete(run)
    await db.commit()


# ── POST /bulk-load — existing batch endpoint (bug fixed) ─────────────────────

@router.post(
    "/bulk-load",
    response_model=BulkLoadResponse,
    dependencies=[Depends(require_scope(["mes:write"]))],
    summary="Carga masiva de corridas de producción planificadas",
)
async def bulk_load_planning(
    entries: List[PlanningEntry],
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    scheduled = 0
    skipped = 0
    errors: list[dict] = []

    for idx, entry in enumerate(entries):
        async with db.begin_nested() as sp:
            try:
                wo = (await db.execute(
                    select(WorkOrder).where(
                        WorkOrder.id == entry.work_order_id,
                        WorkOrder.company_id == company_id,
                    )
                )).scalar_one_or_none()
                if not wo:
                    raise ValueError(f"WorkOrder {entry.work_order_id} not found")

                res = (await db.execute(
                    select(Resource).where(
                        Resource.id == entry.resource_id,
                        Resource.company_id == company_id,
                    )
                )).scalar_one_or_none()
                if not res:
                    raise ValueError(f"Resource {entry.resource_id} not found")

                conflict = (await db.execute(
                    select(ProductionRun).where(
                        ProductionRun.resource_id == entry.resource_id,
                        ProductionRun.shift_id == entry.shift_id,
                        ProductionRun.date == entry.production_date,  # FIX: was entry.date
                        ProductionRun.company_id == company_id,
                    )
                )).scalar_one_or_none()
                if conflict:
                    raise ValueError(
                        f"Resource {entry.resource_id} already has a run on {entry.production_date}"
                    )

                db.add(ProductionRun(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    tenant_id=company_id,
                    work_order_id=entry.work_order_id,
                    resource_id=entry.resource_id,
                    shift_id=entry.shift_id,
                    date=entry.production_date,         # FIX: was entry.date
                    planned_quantity=entry.planned_quantity,
                    actual_quantity=0,
                    # FIX: removed status="SCHEDULED" — field does not exist on model
                ))
                await db.flush()
                scheduled += 1

            except Exception as exc:
                await sp.rollback()
                skipped += 1
                errors.append({"index": idx, "reason": str(exc)})

    await db.commit()
    return BulkLoadResponse(scheduled=scheduled, skipped=skipped, errors=errors)
