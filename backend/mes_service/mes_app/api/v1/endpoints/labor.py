from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional
from datetime import datetime, date, timezone
import uuid

from common.infrastructure.database import get_db
from common.exceptions import NotFoundException
from common.responses import ApiResponse
from common.security.dependencies import require_scope

from mes_app.dependencies import get_current_company, get_hcm_client, get_labor_density_service
from mes_app.models.labor import Labor, LaborType, LaborCategory
from mes_app.models.production_run import ProductionRun
from mes_app.models.facility import Facility
from mes_app.models.production_area import ProductionArea
from mes_app.models.resource import Resource
from mes_app.models.hourly_labor_snapshot import HourlyLaborSnapshot
from mes_app.infrastructure.clients.hcm_client import HCMClient
from mes_app.services.labor_density_service import LaborDensityService

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class LaborRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_number: Optional[int] = None
    clock_in: datetime
    clock_out: Optional[datetime] = None
    is_active_labor: bool
    collaborator_id: Optional[uuid.UUID] = None
    collaborator_name: Optional[str] = None
    assigned_plant: Optional[str] = None
    is_deviation: bool = False

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class LaborClockIn(BaseModel):
    resource_result_id: uuid.UUID
    user_id: uuid.UUID
    employee_number: Optional[int] = None
    type_id: Optional[uuid.UUID] = None
    collaborator_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class LaborClockOut(BaseModel):
    resource_result_id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class LaborTransferRequest(BaseModel):
    collaborator_id: uuid.UUID
    source_production_run_id: uuid.UUID
    destination_production_run_id: uuid.UUID
    reason: Optional[str] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_resource_id_for_run(run_id: uuid.UUID, db: AsyncSession) -> Optional[uuid.UUID]:
    run = await db.get(ProductionRun, run_id)
    return run.resource_id if run else None


async def _get_plant_name_for_run(run_id: uuid.UUID, db: AsyncSession) -> Optional[str]:
    run = await db.get(ProductionRun, run_id)
    if not run:
        return None
    query = (
        select(Facility.name)
        .join(ProductionArea, ProductionArea.facility_id == Facility.id)
        .join(Resource, Resource.production_area_id == ProductionArea.id)
        .where(Resource.id == run.resource_id)
    )
    return (await db.execute(query)).scalar()


# ── Clock-In / Clock-Out ──────────────────────────────────────────────────────

@router.get(
    "/active/{resource_result_id}",
    response_model=List[LaborRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_active_labor(
    resource_result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Listado de personal activo en la línea."""
    query = select(Labor).where(
        and_(
            Labor.resource_result_id == resource_result_id,
            Labor.is_active_labor == True,
        )
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/history/{resource_result_id}",
    response_model=List[LaborRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_labor_history(
    resource_result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Historial completo de labor para el turno."""
    query = select(Labor).where(Labor.resource_result_id == resource_result_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/clock-in", dependencies=[Depends(require_scope(["mes:write"]))])
async def clock_in(
    request: LaborClockIn,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    hcm_client: HCMClient = Depends(get_hcm_client),
    density_svc: LaborDensityService = Depends(get_labor_density_service),
):
    """Registra la entrada de un operador a la línea."""
    existing = await db.scalar(
        select(Labor).where(
            and_(
                Labor.resource_result_id == request.resource_result_id,
                Labor.user_id == request.user_id,
                Labor.is_active_labor == True,
            )
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already clocked in")

    collaborator_name = None
    assigned_plant = None
    warnings = []

    if request.collaborator_id:
        collaborator = await hcm_client.get_collaborator(request.collaborator_id, company_id)
        if collaborator:
            collaborator_name = collaborator.get("full_name") or collaborator.get("fullName")
            assigned_plant = collaborator.get("assigned_plant") or collaborator.get("assignedPlant")
        else:
            collaborator_name = "Unknown Collaborator (HCM Offline)"
            warnings.append("HCM service offline. Using degraded mode.")

    is_deviation = False
    run = await db.get(ProductionRun, request.resource_result_id)
    if run and assigned_plant:
        plant_name = await _get_plant_name_for_run(request.resource_result_id, db)
        if plant_name and plant_name.strip().lower() != assigned_plant.strip().lower():
            is_deviation = True
            warnings.append("Collaborator plant deviation detected.")

    clock_in_time = datetime.now(timezone.utc)
    labor = Labor(
        resource_result_id=request.resource_result_id,
        user_id=request.user_id,
        company_id=company_id,
        employee_number=request.employee_number,
        clock_in=clock_in_time,
        is_active_labor=True,
        type_id=request.type_id,
        collaborator_id=request.collaborator_id,
        collaborator_name=collaborator_name,
        assigned_plant=assigned_plant,
        is_deviation=is_deviation,
    )
    db.add(labor)
    await db.flush()

    # Materializar snapshot para la hora del clock-in
    if run:
        await density_svc.materialize_range(
            production_run_id=run.id,
            resource_id=run.resource_id,
            company_id=company_id,
            clock_in=clock_in_time,
            clock_out=None,
            db=db,
        )

    await db.commit()
    return {"message": "Clock-in successful", "warnings": warnings}


@router.post("/clock-out", dependencies=[Depends(require_scope(["mes:write"]))])
async def clock_out(
    request: LaborClockOut,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    density_svc: LaborDensityService = Depends(get_labor_density_service),
):
    """Registra la salida de un operador."""
    # Fetch active labor to know clock_in (needed for roll-over range)
    active_labor = await db.scalar(
        select(Labor).where(
            and_(
                Labor.resource_result_id == request.resource_result_id,
                Labor.user_id == request.user_id,
                Labor.company_id == company_id,
                Labor.is_active_labor == True,
            )
        )
    )
    if not active_labor:
        raise NotFoundException("Active labor record not found")

    clock_out_time = datetime.now(timezone.utc)
    active_labor.clock_out = clock_out_time
    active_labor.is_active_labor = False

    # Re-materializar todas las horas afectadas (roll-over fix)
    run = await db.get(ProductionRun, request.resource_result_id)
    if run:
        await density_svc.materialize_range(
            production_run_id=run.id,
            resource_id=run.resource_id,
            company_id=company_id,
            clock_in=active_labor.clock_in,
            clock_out=clock_out_time,
            db=db,
        )

    await db.commit()
    return {"message": "Clock-out successful"}


# ── Transfer (atómico: cierra origen + abre destino) ─────────────────────────

@router.post("/transfer", dependencies=[Depends(require_scope(["mes:write"]))])
async def transfer_collaborator(
    request: LaborTransferRequest,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    density_svc: LaborDensityService = Depends(get_labor_density_service),
):
    """
    Traslado atómico de un colaborador entre recursos.

    Orphan Transfer rule (Tip #3): validar destino ANTES de mutar origen.
    Si el destino no existe, abortar sin tocar el registro activo del origen.
    """
    # Paso 1: Validar destino antes de cualquier mutación
    dest_run = await db.get(ProductionRun, request.destination_production_run_id)
    if not dest_run or dest_run.company_id != company_id:
        raise HTTPException(
            status_code=422,
            detail="Destination production run not found or access denied",
        )

    # Paso 2: Localizar Labor activo en el origen
    active_labor = await db.scalar(
        select(Labor).where(
            Labor.production_run_id == request.source_production_run_id,
            Labor.collaborator_id == request.collaborator_id,
            Labor.company_id == company_id,
            Labor.is_active_labor == True,
        )
    )
    if not active_labor:
        raise HTTPException(
            status_code=404,
            detail="No active labor record found for collaborator at source production run",
        )

    transfer_time = datetime.now(timezone.utc)

    # Paso 3: Cerrar Labor en origen
    original_clock_in = active_labor.clock_in
    active_labor.clock_out = transfer_time
    active_labor.is_active_labor = False

    # Paso 4: Re-materializar horas del origen (desde clock_in original hasta ahora)
    source_run = await db.get(ProductionRun, request.source_production_run_id)
    if source_run:
        await density_svc.materialize_range(
            production_run_id=source_run.id,
            resource_id=source_run.resource_id,
            company_id=company_id,
            clock_in=original_clock_in,
            clock_out=transfer_time,
            db=db,
        )

    # Paso 5: Encontrar (o dejar None) el LaborType con category=TRANSFER
    transfer_type = await db.scalar(
        select(LaborType).where(
            LaborType.category == LaborCategory.TRANSFER.value,
            LaborType.company_id == company_id,
        )
    )

    # Paso 6: Crear nuevo Labor en destino
    new_labor = Labor(
        production_run_id=request.destination_production_run_id,
        user_id=active_labor.user_id,
        company_id=company_id,
        collaborator_id=request.collaborator_id,
        collaborator_name=active_labor.collaborator_name,
        assigned_plant=active_labor.assigned_plant,
        clock_in=transfer_time,
        is_active_labor=True,
        type_id=transfer_type.id if transfer_type else None,
        is_deviation=active_labor.is_deviation,
    )
    db.add(new_labor)
    await db.flush()

    # Paso 7: Materializar hora actual en destino
    await density_svc.materialize_range(
        production_run_id=dest_run.id,
        resource_id=dest_run.resource_id,
        company_id=company_id,
        clock_in=transfer_time,
        clock_out=None,
        db=db,
    )

    await db.commit()
    return {
        "message": "Transfer successful",
        "new_labor_id": str(new_labor.id),
        "transfer_time": transfer_time.isoformat(),
    }


# ── Headcount actual (foto en tiempo real) ────────────────────────────────────

@router.get(
    "/headcount/{resource_id}",
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_headcount(
    resource_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Foto actual del recurso: headcount subdividido por estado de labor.

    Responde con: active, on_permit, transferred_in, total_rostered + lista de colaboradores.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    labors_stmt = (
        select(Labor, LaborType)
        .outerjoin(LaborType, Labor.type_id == LaborType.id)
        .join(ProductionRun, Labor.production_run_id == ProductionRun.id)
        .where(
            ProductionRun.resource_id == resource_id,
            ProductionRun.date == today,
            Labor.company_id == company_id,
            Labor.is_active_labor == True,
        )
    )
    rows = (await db.execute(labors_stmt)).all()

    headcount_active = 0
    headcount_on_permit = 0
    headcount_transferred_in = 0
    collaborators = []

    for labor, labor_type in rows:
        category = LaborCategory.ACTIVE
        if labor_type and labor_type.category:
            try:
                category = LaborCategory(labor_type.category)
            except ValueError:
                category = LaborCategory.ACTIVE

        if category == LaborCategory.PERMIT:
            headcount_on_permit += 1
            status = "ON_PERMIT"
        elif category == LaborCategory.TRANSFER:
            headcount_transferred_in += 1
            status = "TRANSFERRED_IN"
        else:
            headcount_active += 1
            status = "ACTIVE"

        collaborators.append({
            "id": str(labor.collaborator_id) if labor.collaborator_id else None,
            "name": labor.collaborator_name or "Unknown",
            "status": status,
            "clock_in": labor.clock_in.strftime("%H:%M"),
            "is_deviation": labor.is_deviation,
        })

    return {
        "resource_id": str(resource_id),
        "snapshot_time": now.isoformat(),
        "headcount": {
            "active": headcount_active,
            "on_permit": headcount_on_permit,
            "transferred_in": headcount_transferred_in,
            "total_rostered": len(rows),
        },
        "collaborators": collaborators,
    }


# ── Headcount histórico horario (para gráfica del supervisor) ─────────────────

@router.get(
    "/headcount-history/{resource_id}",
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_headcount_history(
    resource_id: uuid.UUID,
    query_date: Optional[date] = Query(default=None, alias="date", description="Fecha (default: hoy)"),
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Serie temporal horaria de headcount para un recurso.
    Lee de mes_hourly_labor_snapshots — O(1) sin scan de mes_labors.

    Responde: { date, series: [{hour, label, active, on_permit, transferred_in, ...}] }
    """
    target_date = query_date or date.today()

    stmt = (
        select(HourlyLaborSnapshot)
        .where(
            HourlyLaborSnapshot.resource_id == resource_id,
            HourlyLaborSnapshot.date == target_date,
            HourlyLaborSnapshot.company_id == company_id,
        )
        .order_by(HourlyLaborSnapshot.hour)
    )
    snapshots = (await db.execute(stmt)).scalars().all()

    series = [
        {
            "hour": s.hour,
            "label": f"{s.hour:02d}:00",
            "active": s.headcount_active,
            "on_permit": s.headcount_on_permit,
            "transferred_in": s.headcount_transferred_in,
            "transferred_out": s.headcount_transferred_out,
            "total": s.headcount_active + s.headcount_on_permit,
            "total_labor_minutes": float(s.total_labor_minutes),
            "paid_hrs": float(s.paid_hrs),
        }
        for s in snapshots
    ]

    return {
        "resource_id": str(resource_id),
        "date": target_date.isoformat(),
        "series": series,
    }
