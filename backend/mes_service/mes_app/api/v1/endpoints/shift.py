"""
MES Shifts — CRUD endpoints for Shift + ShiftBreak (Phase 156-C).

Routes (prefix: /api/v1/mes/shifts):
  GET    /              → list active shifts for company
  POST   /              → create shift
  GET    /{shift_id}    → get shift with breaks
  PATCH  /{shift_id}    → update shift fields
  DELETE /{shift_id}    → soft-delete (is_active=False)
  GET    /{shift_id}/breaks        → list breaks
  POST   /{shift_id}/breaks        → create break
  DELETE /{shift_id}/breaks/{brk}  → hard-delete break
"""
import uuid
from datetime import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.infrastructure.database import get_db
from common.context import request_context
from mes_app.models.shift import Shift
from mes_app.models.shift_break import ShiftBreak

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ShiftBreakRead(BaseModel):
    id: uuid.UUID
    code: str
    label: str
    break_type: Optional[str] = None
    start_time: str
    end_time: str
    duration_minutes: int
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_break(cls, sb: ShiftBreak) -> "ShiftBreakRead":
        return cls(
            id=sb.id,
            code=sb.code,
            label=sb.label,
            break_type=sb.break_type,
            start_time=sb.start_time.strftime("%H:%M"),
            end_time=sb.end_time.strftime("%H:%M"),
            duration_minutes=sb.duration_minutes,
        )


class ShiftRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    start_time: str
    end_time: str
    is_overnight: bool
    break_minutes: int
    is_active: bool
    resource_id: Optional[uuid.UUID] = None
    breaks: List[ShiftBreakRead] = []
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, s: Shift) -> "ShiftRead":
        return cls(
            id=s.id,
            code=s.code,
            name=s.name,
            start_time=s.start_time.strftime("%H:%M"),
            end_time=s.end_time.strftime("%H:%M"),
            is_overnight=s.is_overnight,
            break_minutes=s.break_minutes,
            is_active=s.is_active,
            resource_id=s.resource_id,
            breaks=[ShiftBreakRead.from_orm_break(b) for b in (s.breaks or [])],
        )


class ShiftCreate(BaseModel):
    code: str = Field(max_length=20)
    name: str = Field(max_length=100)
    start_time: str = Field(description="HH:MM format")
    end_time: str = Field(description="HH:MM format")
    is_overnight: bool = False
    break_minutes: int = Field(default=60, ge=0, le=480)
    resource_id: Optional[uuid.UUID] = None


class ShiftUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_overnight: Optional[bool] = None
    break_minutes: Optional[int] = Field(None, ge=0, le=480)
    is_active: Optional[bool] = None
    resource_id: Optional[uuid.UUID] = None


class ShiftBreakCreate(BaseModel):
    code: str = Field(max_length=15)
    label: str = Field(max_length=50)
    break_type: Optional[str] = Field(None, pattern="^(BREAK|MEAL|MAINTENANCE)$")
    start_time: str = Field(description="HH:MM format")
    end_time: str = Field(description="HH:MM format")
    duration_minutes: int = Field(ge=1, le=240)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _company_id() -> uuid.UUID:
    ctx = request_context.get()
    if not ctx or not ctx.company_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid company context required",
        )
    return ctx.company_id


def _parse_time(t_str: str, field_name: str) -> time:
    try:
        h, m = t_str.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} must be in HH:MM format",
        )


async def _get_shift_or_404(shift_id: uuid.UUID, company_id: uuid.UUID,
                             db: AsyncSession) -> Shift:
    result = await db.execute(
        select(Shift).where(Shift.id == shift_id, Shift.company_id == company_id)
    )
    shift = result.scalars().first()
    if not shift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Shift {shift_id} not found")
    return shift


# ── Shift endpoints ───────────────────────────────────────────────────────────

@router.get("/", response_model=List[ShiftRead])
async def list_shifts(db: AsyncSession = Depends(get_db)):
    """List all active shifts for the authenticated company."""
    company_id = _company_id()
    result = await db.execute(
        select(Shift).where(Shift.company_id == company_id, Shift.is_active == True)
    )
    return [ShiftRead.from_orm(s) for s in result.scalars().all()]


@router.post("/", response_model=ShiftRead, status_code=status.HTTP_201_CREATED)
async def create_shift(body: ShiftCreate, db: AsyncSession = Depends(get_db)):
    """Create a new shift for the company."""
    company_id = _company_id()

    # Check duplicate code within company
    existing = (await db.execute(
        select(Shift).where(Shift.company_id == company_id, Shift.code == body.code)
    )).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Shift with code '{body.code}' already exists for this company",
        )

    shift = Shift(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        code=body.code,
        name=body.name,
        start_time=_parse_time(body.start_time, "start_time"),
        end_time=_parse_time(body.end_time, "end_time"),
        is_overnight=body.is_overnight,
        break_minutes=body.break_minutes,
        resource_id=body.resource_id,
        is_active=True,
    )
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    return ShiftRead.from_orm(shift)


@router.get("/{shift_id}", response_model=ShiftRead)
async def get_shift(shift_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a single shift with its breaks."""
    company_id = _company_id()
    shift = await _get_shift_or_404(shift_id, company_id, db)
    return ShiftRead.from_orm(shift)


@router.patch("/{shift_id}", response_model=ShiftRead)
async def update_shift(
    shift_id: uuid.UUID,
    body: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update shift fields (partial update)."""
    company_id = _company_id()
    shift = await _get_shift_or_404(shift_id, company_id, db)

    if body.name is not None:
        shift.name = body.name
    if body.start_time is not None:
        shift.start_time = _parse_time(body.start_time, "start_time")
    if body.end_time is not None:
        shift.end_time = _parse_time(body.end_time, "end_time")
    if body.is_overnight is not None:
        shift.is_overnight = body.is_overnight
    if body.break_minutes is not None:
        shift.break_minutes = body.break_minutes
    if body.is_active is not None:
        shift.is_active = body.is_active
    if body.resource_id is not None:
        shift.resource_id = body.resource_id

    await db.commit()
    await db.refresh(shift)
    return ShiftRead.from_orm(shift)


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(shift_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Soft-delete a shift (sets is_active=False)."""
    company_id = _company_id()
    shift = await _get_shift_or_404(shift_id, company_id, db)
    shift.is_active = False
    await db.commit()


# ── ShiftBreak sub-resource endpoints ─────────────────────────────────────────

@router.get("/{shift_id}/breaks", response_model=List[ShiftBreakRead])
async def list_breaks(shift_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """List all breaks for a shift."""
    company_id = _company_id()
    await _get_shift_or_404(shift_id, company_id, db)

    result = await db.execute(
        select(ShiftBreak).where(ShiftBreak.shift_id == shift_id)
        .order_by(ShiftBreak.start_time)
    )
    return [ShiftBreakRead.from_orm_break(b) for b in result.scalars().all()]


@router.post("/{shift_id}/breaks", response_model=ShiftBreakRead,
             status_code=status.HTTP_201_CREATED)
async def create_break(
    shift_id: uuid.UUID,
    body: ShiftBreakCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a break to a shift."""
    company_id = _company_id()
    await _get_shift_or_404(shift_id, company_id, db)

    brk = ShiftBreak(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        shift_id=shift_id,
        code=body.code,
        label=body.label,
        break_type=body.break_type or "BREAK",
        start_time=_parse_time(body.start_time, "start_time"),
        end_time=_parse_time(body.end_time, "end_time"),
        duration_minutes=body.duration_minutes,
    )
    db.add(brk)
    await db.commit()
    await db.refresh(brk)
    return ShiftBreakRead.from_orm_break(brk)


@router.delete("/{shift_id}/breaks/{break_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_break(
    shift_id: uuid.UUID,
    break_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Hard-delete a ShiftBreak."""
    company_id = _company_id()
    await _get_shift_or_404(shift_id, company_id, db)

    result = await db.execute(
        select(ShiftBreak).where(
            ShiftBreak.id == break_id,
            ShiftBreak.shift_id == shift_id,
        )
    )
    brk = result.scalars().first()
    if not brk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Break {break_id} not found in shift {shift_id}")
    await db.delete(brk)
    await db.commit()
