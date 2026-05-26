from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.dependencies import get_db, get_current_company
from mes_app.models.downtime import Downtime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from datetime import datetime
from sqlalchemy import select, update, and_
from typing import List, Optional
from common.exceptions import NotFoundException
from common.responses import ApiResponse
from common.security.dependencies import require_scope, get_current_active_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class DowntimeRead(BaseModel):
    id: uuid.UUID
    status: str
    start_at: datetime
    responded_at: Optional[datetime]
    closed_at: Optional[datetime]
    admin_closed_at: Optional[datetime]
    description: Optional[str]
    action_taken: Optional[str]
    root_cause: Optional[str]
    mttr_minutes: float
    escalation_level: int

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class DowntimeAdminClose(BaseModel):
    root_cause: str = Field(description="Final root cause analysis")

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DowntimeOpen(BaseModel):
    resource_result_id: uuid.UUID
    reason_id: Optional[uuid.UUID] = None
    description: Optional[str] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/open",
    response_model=DowntimeRead,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def open_downtime(
    request: DowntimeOpen,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Abre un nuevo paro en línea."""
    downtime = Downtime(
        resource_result_id=request.resource_result_id,
        reason_id=request.reason_id,
        description=request.description,
        company_id=company_id,
        start_at=datetime.now(),
        status="OPEN",
    )
    db.add(downtime)
    await db.commit()
    await db.refresh(downtime)
    return downtime


@router.patch("/{downtime_id}/respond")
async def respond_downtime(
    downtime_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    current_user=Depends(get_current_active_user),
    _scope=Depends(require_scope(["mes:write"])),
    db: AsyncSession = Depends(get_db),
):
    """Marca el inicio de atención técnica. El técnico se extrae del JWT."""
    tech_user_id = uuid.UUID(current_user.sub)
    query = update(Downtime).where(
        and_(
            Downtime.id == downtime_id,
            Downtime.company_id == company_id,
            Downtime.status == "OPEN",
        )
    ).values(
        responded_at=datetime.now(),
        assign_to_user_id=tech_user_id,
        status="RESPONDED",
        updated_at=datetime.now(),
    )
    result = await db.execute(query)
    await db.commit()
    if result.rowcount == 0:
        raise NotFoundException("Downtime not found or not in OPEN status")
    return {"message": "Downtime responded"}


@router.patch(
    "/{downtime_id}/close",
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def close_downtime(
    downtime_id: uuid.UUID,
    action: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Cierre técnico del paro. Filtrado por company_id del JWT."""
    query = update(Downtime).where(
        and_(
            Downtime.id == downtime_id,
            Downtime.company_id == company_id,
        )
    ).values(
        closed_at=datetime.now(),
        action_taken=action,
        status="TECH_CLOSED",
        updated_at=datetime.now(),
    )
    result = await db.execute(query)
    await db.commit()
    if result.rowcount == 0:
        raise NotFoundException("Downtime not found")

    downtime_obj = await db.get(Downtime, downtime_id)
    if downtime_obj:
        from mes_app.services.event_publisher import EventPublisher
        await EventPublisher.publish("MES_DOWNTIME_CLOSED", {
            "downtime_id": str(downtime_id),
            "closed_at": datetime.now().isoformat(),
            "status": "TECH_CLOSED",
            "station_id": str(downtime_obj.resource_result_id),
            "company_id": str(downtime_obj.company_id),
        })

    return {"message": "Downtime closed"}


@router.patch("/{downtime_id}/admin-close")
async def admin_close_downtime(
    downtime_id: uuid.UUID,
    request: DowntimeAdminClose,
    company_id: uuid.UUID = Depends(get_current_company),
    current_user=Depends(get_current_active_user),
    _scope=Depends(require_scope(["mes:admin", "mes:write"])),
    db: AsyncSession = Depends(get_db),
):
    """Cierre administrativo. El supervisor se extrae del JWT."""
    admin_user_id = uuid.UUID(current_user.sub)
    query = update(Downtime).where(
        and_(
            Downtime.id == downtime_id,
            Downtime.company_id == company_id,
        )
    ).values(
        admin_closed_at=datetime.now(),
        admin_user_id=admin_user_id,
        root_cause=request.root_cause,
        status="ADMIN_CLOSED",
        updated_at=datetime.now(),
    )
    result = await db.execute(query)
    await db.commit()
    if result.rowcount == 0:
        raise NotFoundException("Downtime not found")

    from mes_app.services.event_publisher import EventPublisher
    await EventPublisher.publish("MES_DOWNTIME_ADMIN_CLOSED", {
        "downtime_id": str(downtime_id),
        "admin_user_id": str(admin_user_id),
        "status": "ADMIN_CLOSED",
    })

    return {"message": "Downtime administratively closed"}


@router.get(
    "/active/{resource_result_id}",
    response_model=List[DowntimeRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_active_downtimes(
    resource_result_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Listado de paros abiertos o en proceso. Filtrado por company_id del JWT."""
    query = select(Downtime).where(
        and_(
            Downtime.resource_result_id == resource_result_id,
            Downtime.company_id == company_id,
            Downtime.status.in_(["OPEN", "RESPONDED"]),
        )
    )
    result = await db.execute(query)
    return result.scalars().all()
