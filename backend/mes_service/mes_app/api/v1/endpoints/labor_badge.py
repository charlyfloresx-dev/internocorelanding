"""
Shop-Floor Badge Authentication — Phase 170

POST /mes/labor/clock-in-by-badge
  Resolves RFID/QR/Barcode to a collaborator and executes:
    - CLOCK_IN  → new active labor record
    - TRANSFER  → auto-closes origin, opens destination (Iron Wall: no cross-service FK)
    - ALREADY_CLOCKED_IN → idempotent no-op with 200

GET/POST/PATCH/DELETE /mes/labor/badges  — Admin CRUD for badge registration
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.infrastructure.database import get_db
from common.responses import ApiResponse
from common.security.dependencies import require_scope

from mes_app.dependencies import get_current_company, get_hcm_client, get_labor_density_service
from mes_app.models.collaborator_badge import CollaboratorBadge
from mes_app.models.labor import Labor, LaborType, LaborCategory
from mes_app.models.production_run import ProductionRun
from mes_app.models.resource import Resource
from mes_app.services.labor_density_service import LaborDensityService
from mes_app.infrastructure.clients.hcm_client import HCMClient

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class BadgeClockInRequest(BaseModel):
    resource_code: str
    production_run_id: Optional[uuid.UUID] = None  # auto-resolved from resource_code if omitted
    badge_raw_value: str
    client_timestamp: Optional[datetime] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BadgeClockInResponse(BaseModel):
    status: str            # SUCCESS | ERROR
    action: str            # CLOCK_IN | TRANSFER | ALREADY_CLOCKED_IN
    collaborator: dict
    timestamp: str


class BadgeCreate(BaseModel):
    collaborator_id: uuid.UUID
    badge_raw_value: str
    badge_type: str = "RFID"   # BARCODE | QR | RFID
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class BadgeRead(BaseModel):
    id: uuid.UUID
    collaborator_id: uuid.UUID
    collaborator_name: str
    employee_number: Optional[int] = None
    badge_raw_value: str
    badge_type: str
    is_active: bool
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)


class BadgeUpdate(BaseModel):
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ── Clock-in by Badge ─────────────────────────────────────────────────────────

@router.post(
    "/clock-in-by-badge",
    response_model=BadgeClockInResponse,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def clock_in_by_badge(
    request: BadgeClockInRequest,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    density_svc: LaborDensityService = Depends(get_labor_density_service),
    hcm_client: HCMClient = Depends(get_hcm_client),
):
    """
    Autenticación express en piso de manufactura.

    Acepta el string raw leído por RFID/QR/Barcode (modo HID — keyboard emulation).
    Ejecuta la acción correcta sin intervención del operador:
      - CLOCK_IN            → primer check-in del día en este recurso
      - TRANSFER            → ya activo en otro run → cierre automático + apertura destino
      - ALREADY_CLOCKED_IN  → idempotente, retorna 200 con estado actual
    """
    now = datetime.now(timezone.utc)

    # 1. Resolver credencial física → colaborador
    # Strip whitespace/newlines — HID scanners and QR decoders may append \n or spaces
    clean_badge = request.badge_raw_value.strip()

    badge = await db.scalar(
        select(CollaboratorBadge).where(
            CollaboratorBadge.badge_raw_value == clean_badge,
            CollaboratorBadge.company_id == company_id,
            CollaboratorBadge.is_active == True,
        )
    )

    # ── Fallback: resolve by internal_id via HCM + auto-register badge ──────
    # If no badge record exists, the raw value might be the collaborator's
    # internal_id (e.g. QR codes printed with internal_id).
    # We call HCM validate-scan and register the badge on first use.
    if not badge:
        hcm_match = await hcm_client.resolve_by_internal_id(clean_badge, company_id)
        if hcm_match and hcm_match.get("collaborator_id"):
            badge = CollaboratorBadge(
                company_id=company_id,
                tenant_id=company_id,
                collaborator_id=uuid.UUID(str(hcm_match["collaborator_id"])),
                collaborator_name=hcm_match.get("full_name", clean_badge),
                badge_raw_value=clean_badge,
                badge_type="BARCODE",
                is_active=True,
            )
            db.add(badge)
            await db.flush()   # get id without committing yet
        else:
            raise HTTPException(status_code=404, detail="Credencial no registrada o inactiva")

    # Validar expiración
    if badge.expires_at and badge.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=403, detail="Credencial expirada")

    # 2. Verificar si el colaborador ya tiene labor activa
    active_labor = await db.scalar(
        select(Labor).where(
            Labor.collaborator_id == badge.collaborator_id,
            Labor.company_id == company_id,
            Labor.is_active_labor == True,
        )
    )

    # Resolver production_run: explícito o auto-detect por resource_code + hoy
    if request.production_run_id:
        dest_run = await db.get(ProductionRun, request.production_run_id)
        if not dest_run or dest_run.company_id != company_id:
            raise HTTPException(status_code=422, detail="Production run de destino no encontrado")
    else:
        resource = await db.scalar(
            select(Resource).where(
                Resource.code == request.resource_code,
                Resource.company_id == company_id,
            )
        )
        if not resource:
            raise HTTPException(status_code=404, detail=f"Recurso '{request.resource_code}' no encontrado")
        today = now.date()
        dest_run = await db.scalar(
            select(ProductionRun).where(
                ProductionRun.resource_id == resource.id,
                ProductionRun.date == today,
                ProductionRun.company_id == company_id,
                ProductionRun.status != "COMPLETED",
            ).order_by(ProductionRun.created_at.desc())
        )
        if not dest_run:
            raise HTTPException(
                status_code=422,
                detail=f"Sin producción activa para '{request.resource_code}' hoy",
            )

    collaborator_info = {
        "employee_number": badge.employee_number,
        "full_name": badge.collaborator_name,
        "collaborator_id": str(badge.collaborator_id),
        "category_assigned": LaborCategory.ACTIVE.value,
    }

    # 3. Determinar acción
    if active_labor and active_labor.production_run_id == request.production_run_id:
        # Ya registrado aquí — idempotente
        return BadgeClockInResponse(
            status="SUCCESS",
            action="ALREADY_CLOCKED_IN",
            collaborator=collaborator_info,
            timestamp=now.isoformat(),
        )

    if active_labor:
        # Está en otro recurso → traslado automático
        original_clock_in = active_labor.clock_in
        active_labor.clock_out = now
        active_labor.is_active_labor = False

        source_run = await db.get(ProductionRun, active_labor.production_run_id)
        if source_run:
            await density_svc.materialize_range(
                production_run_id=source_run.id,
                resource_id=source_run.resource_id,
                company_id=company_id,
                clock_in=original_clock_in,
                clock_out=now,
                db=db,
            )

        # LaborType con categoría TRANSFER (si existe)
        transfer_type = await db.scalar(
            select(LaborType).where(
                LaborType.category == LaborCategory.TRANSFER.value,
                LaborType.company_id == company_id,
            )
        )
        new_labor = Labor(
            production_run_id=request.production_run_id,
            user_id=badge.collaborator_id,
            company_id=company_id,
            collaborator_id=badge.collaborator_id,
            collaborator_name=badge.collaborator_name,
            employee_number=badge.employee_number,
            clock_in=now,
            is_active_labor=True,
            type_id=transfer_type.id if transfer_type else None,
            is_deviation=False,
        )
        db.add(new_labor)
        await db.flush()

        await density_svc.materialize_range(
            production_run_id=dest_run.id,
            resource_id=dest_run.resource_id,
            company_id=company_id,
            clock_in=now,
            clock_out=None,
            db=db,
        )
        await db.commit()

        collaborator_info["category_assigned"] = LaborCategory.TRANSFER.value
        return BadgeClockInResponse(
            status="SUCCESS",
            action="TRANSFER",
            collaborator=collaborator_info,
            timestamp=now.isoformat(),
        )

    # Clock-In regular
    new_labor = Labor(
        production_run_id=request.production_run_id,
        user_id=badge.collaborator_id,
        company_id=company_id,
        collaborator_id=badge.collaborator_id,
        collaborator_name=badge.collaborator_name,
        employee_number=badge.employee_number,
        clock_in=now,
        is_active_labor=True,
        is_deviation=False,
    )
    db.add(new_labor)
    await db.flush()

    await density_svc.materialize_range(
        production_run_id=dest_run.id,
        resource_id=dest_run.resource_id,
        company_id=company_id,
        clock_in=now,
        clock_out=None,
        db=db,
    )
    await db.commit()

    return BadgeClockInResponse(
        status="SUCCESS",
        action="CLOCK_IN",
        collaborator=collaborator_info,
        timestamp=now.isoformat(),
    )


# ── Badge CRUD (administración) ────────────────────────────────────────────────

@router.get(
    "/badges",
    response_model=ApiResponse[List[BadgeRead]],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def list_badges(
    collaborator_id: Optional[uuid.UUID] = None,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CollaboratorBadge).where(CollaboratorBadge.company_id == company_id)
    if collaborator_id:
        stmt = stmt.where(CollaboratorBadge.collaborator_id == collaborator_id)
    badges = (await db.execute(stmt)).scalars().all()
    return ApiResponse(status="success", data=badges, message=f"{len(badges)} badges found")


@router.post(
    "/badges",
    response_model=ApiResponse[BadgeRead],
    status_code=201,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def create_badge(
    payload: BadgeCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    hcm_client: HCMClient = Depends(get_hcm_client),
):
    """
    Registra una credencial física.
    Enriquece con datos de HCM (nombre, employee_number) en tiempo de registro,
    no en cada scan — soporta modo degradado si HCM está caído.
    """
    existing = await db.scalar(
        select(CollaboratorBadge).where(
            CollaboratorBadge.badge_raw_value == payload.badge_raw_value,
            CollaboratorBadge.company_id == company_id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Badge ya registrado para esta empresa")

    # Enriquecer con HCM (degraded: usa defaults si falla)
    collaborator_name = "Colaborador"
    employee_number = None
    hcm_data = await hcm_client.get_collaborator(payload.collaborator_id, company_id)
    if hcm_data:
        collaborator_name = hcm_data.get("full_name") or hcm_data.get("fullName") or collaborator_name
        employee_number = hcm_data.get("employee_number") or hcm_data.get("employeeNumber")

    badge = CollaboratorBadge(
        company_id=company_id,
        collaborator_id=payload.collaborator_id,
        collaborator_name=collaborator_name,
        employee_number=employee_number,
        badge_raw_value=payload.badge_raw_value,
        badge_type=payload.badge_type,
        is_active=True,
        expires_at=payload.expires_at,
    )
    db.add(badge)
    await db.commit()
    await db.refresh(badge)
    return ApiResponse(status="success", data=badge, message="Badge creado")


@router.patch(
    "/badges/{badge_id}",
    response_model=ApiResponse[BadgeRead],
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def update_badge(
    badge_id: uuid.UUID,
    payload: BadgeUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    badge = await db.scalar(
        select(CollaboratorBadge).where(
            CollaboratorBadge.id == badge_id,
            CollaboratorBadge.company_id == company_id,
        )
    )
    if not badge:
        raise HTTPException(status_code=404, detail="Badge no encontrado")
    if payload.is_active is not None:
        badge.is_active = payload.is_active
    if payload.expires_at is not None:
        badge.expires_at = payload.expires_at
    await db.commit()
    await db.refresh(badge)
    return ApiResponse(status="success", data=badge, message="Badge actualizado")


@router.delete(
    "/badges/{badge_id}",
    response_model=ApiResponse[bool],
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def delete_badge(
    badge_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    badge = await db.scalar(
        select(CollaboratorBadge).where(
            CollaboratorBadge.id == badge_id,
            CollaboratorBadge.company_id == company_id,
        )
    )
    if not badge:
        raise HTTPException(status_code=404, detail="Badge no encontrado")
    badge.is_active = False
    await db.commit()
    return ApiResponse(status="success", data=True, message="Badge desactivado")
