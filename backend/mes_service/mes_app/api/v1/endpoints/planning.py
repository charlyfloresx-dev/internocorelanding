from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from mes_app.dependencies import get_current_company
from mes_app.models.production_run import ProductionRun
from mes_app.models.work_order import WorkOrder
from mes_app.models.resource import Resource
from mes_app.schemas.planning import PlanningEntry, BulkLoadResponse

router = APIRouter()


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
    """
    Crea múltiples ProductionRun a partir de una lista de entradas de planificación.

    Cada entrada se procesa atómicamente con begin_nested(). Un fallo en una entrada
    no aborta las demás — se acumula en `errors` y el contador `skipped` sube.

    company_id se extrae exclusivamente del JWT (Muro de Hierro — nunca del body).
    """
    scheduled = 0
    skipped = 0
    errors: list[dict] = []

    for idx, entry in enumerate(entries):
        async with db.begin_nested() as sp:
            try:
                # 1. Validate WorkOrder belongs to this company
                wo_result = await db.execute(
                    select(WorkOrder).where(
                        WorkOrder.id == entry.work_order_id,
                        WorkOrder.company_id == company_id,
                    )
                )
                wo = wo_result.scalar_one_or_none()
                if not wo:
                    raise ValueError(f"WorkOrder {entry.work_order_id} not found for this company")

                # 2. Validate Resource belongs to this company
                res_result = await db.execute(
                    select(Resource).where(
                        Resource.id == entry.resource_id,
                        Resource.company_id == company_id,
                    )
                )
                res = res_result.scalar_one_or_none()
                if not res:
                    raise ValueError(f"Resource {entry.resource_id} not found for this company")

                # 3. Conflict check: same resource/shift/date combination
                conflict_result = await db.execute(
                    select(ProductionRun).where(
                        ProductionRun.resource_id == entry.resource_id,
                        ProductionRun.shift_id == entry.shift_id,
                        ProductionRun.date == entry.date,
                        ProductionRun.company_id == company_id,
                    )
                )
                if conflict_result.scalar_one_or_none():
                    raise ValueError(
                        f"Resource {entry.resource_id} already has a run on {entry.date} shift {entry.shift_id}"
                    )

                # 4. Create the scheduled run
                run = ProductionRun(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    work_order_id=entry.work_order_id,
                    resource_id=entry.resource_id,
                    shift_id=entry.shift_id,
                    date=entry.date,
                    planned_quantity=entry.planned_quantity,
                    actual_quantity=0,
                    status="SCHEDULED",
                )
                db.add(run)
                await db.flush()
                scheduled += 1

            except Exception as exc:
                await sp.rollback()
                skipped += 1
                errors.append({"index": idx, "reason": str(exc)})

    await db.commit()
    return BulkLoadResponse(scheduled=scheduled, skipped=skipped, errors=errors)
