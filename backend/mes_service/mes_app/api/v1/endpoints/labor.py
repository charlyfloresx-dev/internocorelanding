from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.dependencies import get_db, get_current_company
from mes_app.models.labor import Labor
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from datetime import datetime
from sqlalchemy import select, update, and_
from typing import List, Optional

from common.exceptions import NotFoundException
from common.responses import ApiResponse
from common.security.dependencies import require_scope

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class LaborRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_number: Optional[int] = None
    clock_in: datetime
    clock_out: Optional[datetime] = None
    is_active_labor: bool

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )


class LaborClockIn(BaseModel):
    resource_result_id: uuid.UUID
    user_id: uuid.UUID
    employee_number: Optional[int] = None
    type_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class LaborClockOut(BaseModel):
    resource_result_id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/active/{resource_result_id}",
    response_model=List[LaborRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_active_labor(
    resource_result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retorna el listado de personal activo en la línea."""
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
):
    """Registra la entrada de un operador a la línea."""
    existing = await db.execute(
        select(Labor).where(
            and_(
                Labor.resource_result_id == request.resource_result_id,
                Labor.user_id == request.user_id,
                Labor.is_active_labor == True,
            )
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="User already clocked in")

    labor = Labor(
        resource_result_id=request.resource_result_id,
        user_id=request.user_id,
        company_id=company_id,
        employee_number=request.employee_number,
        clock_in=datetime.now(),
        is_active_labor=True,
        type_id=request.type_id,
    )
    db.add(labor)
    await db.commit()
    return {"message": "Clock-in successful"}


@router.post("/clock-out", dependencies=[Depends(require_scope(["mes:write"]))])
async def clock_out(
    request: LaborClockOut,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Registra la salida de un operador. company_id del JWT garantiza tenant isolation."""
    query = update(Labor).where(
        and_(
            Labor.resource_result_id == request.resource_result_id,
            Labor.user_id == request.user_id,
            Labor.company_id == company_id,
            Labor.is_active_labor == True,
        )
    ).values(
        clock_out=datetime.now(),
        is_active_labor=False,
    )
    result = await db.execute(query)
    await db.commit()

    if result.rowcount == 0:
        raise NotFoundException("Active labor record not found")

    return {"message": "Clock-out successful"}
