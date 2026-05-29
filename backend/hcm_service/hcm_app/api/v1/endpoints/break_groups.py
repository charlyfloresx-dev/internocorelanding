"""
HCM BreakGroups — grupos de descanso escalonados por capacidad de área común.

Rutas (prefix /api/v1/hcm/break-groups):
  GET    /               → list break groups for company
  POST   /               → create break group
  GET    /{id}           → get group with slots
  PATCH  /{id}           → update group
  DELETE /{id}           → soft-delete
  GET    /{id}/slots     → list slots (used by MES ResourceGraphicService HTTP call)
  POST   /{id}/slots     → add slot
  DELETE /{id}/slots/{slot_id} → remove slot
"""
import uuid
from datetime import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hcm_app.core.database import get_db
from hcm_app.models.break_group import BreakGroup, BreakSlot
from common.context import request_context

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class BreakSlotRead(BaseModel):
    id: uuid.UUID
    label: str
    break_type: str
    start_time: str   # "HH:MM"
    end_time: str
    duration_minutes: int
    max_concurrent: int
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_slot(cls, s: BreakSlot) -> "BreakSlotRead":
        return cls(
            id=s.id,
            label=s.label,
            break_type=s.break_type,
            start_time=s.start_time.strftime("%H:%M"),
            end_time=s.end_time.strftime("%H:%M"),
            duration_minutes=s.duration_minutes,
            max_concurrent=s.max_concurrent,
        )


class BreakGroupRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    area_capacity: int
    is_active: bool
    slots: List[BreakSlotRead] = []
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm(cls, g: BreakGroup) -> "BreakGroupRead":
        return cls(
            id=g.id,
            name=g.name,
            description=g.description,
            area_capacity=g.area_capacity,
            is_active=g.is_active,
            slots=[BreakSlotRead.from_orm_slot(s) for s in (g.slots or [])],
        )


class BreakGroupCreate(BaseModel):
    name: str = Field(max_length=100)
    description: Optional[str] = Field(None, max_length=250)
    area_capacity: int = Field(default=0, ge=0)


class BreakGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=250)
    area_capacity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class BreakSlotCreate(BaseModel):
    label: str = Field(max_length=50)
    break_type: str = Field(default="BREAK", pattern="^(BREAK|MEAL|MAINTENANCE)$")
    start_time: str = Field(description="HH:MM")
    end_time: str = Field(description="HH:MM")
    duration_minutes: int = Field(ge=1, le=240)
    max_concurrent: int = Field(default=0, ge=0,
                                 description="Max workers on this break at once (0 = unlimited)")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _company_id() -> uuid.UUID:
    ctx = request_context.get()
    if not ctx or not ctx.company_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Valid company context required")
    return ctx.company_id


def _parse_time(t: str, field: str) -> time:
    try:
        h, m = t.split(":")
        return time(int(h), int(m))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=422, detail=f"{field} must be HH:MM")


async def _get_group(group_id: uuid.UUID, company_id: uuid.UUID,
                     db: AsyncSession) -> BreakGroup:
    result = await db.execute(
        select(BreakGroup).where(BreakGroup.id == group_id,
                                 BreakGroup.company_id == company_id)
    )
    g = result.scalars().first()
    if not g:
        raise HTTPException(status_code=404, detail=f"BreakGroup {group_id} not found")
    return g


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[BreakGroupRead])
async def list_break_groups(db: AsyncSession = Depends(get_db)):
    company_id = _company_id()
    result = await db.execute(
        select(BreakGroup).where(BreakGroup.company_id == company_id,
                                 BreakGroup.is_active == True)
    )
    return [BreakGroupRead.from_orm(g) for g in result.scalars().all()]


@router.post("/", response_model=BreakGroupRead, status_code=201)
async def create_break_group(body: BreakGroupCreate, db: AsyncSession = Depends(get_db)):
    company_id = _company_id()
    g = BreakGroup(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        name=body.name,
        description=body.description,
        area_capacity=body.area_capacity,
    )
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return BreakGroupRead.from_orm(g)


@router.get("/{group_id}", response_model=BreakGroupRead)
async def get_break_group(group_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return BreakGroupRead.from_orm(await _get_group(group_id, _company_id(), db))


@router.patch("/{group_id}", response_model=BreakGroupRead)
async def update_break_group(group_id: uuid.UUID, body: BreakGroupUpdate,
                              db: AsyncSession = Depends(get_db)):
    g = await _get_group(group_id, _company_id(), db)
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(g, field, val)
    await db.commit()
    await db.refresh(g)
    return BreakGroupRead.from_orm(g)


@router.delete("/{group_id}", status_code=204)
async def delete_break_group(group_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    g = await _get_group(group_id, _company_id(), db)
    g.is_active = False
    await db.commit()


# ── Slots ─────────────────────────────────────────────────────────────────────

@router.get("/{group_id}/slots", response_model=List[BreakSlotRead])
async def list_slots(group_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Called by MES ResourceGraphicService when resource.break_group_id is set."""
    company_id = _company_id()
    # Validate group belongs to company
    await _get_group(group_id, company_id, db)
    result = await db.execute(
        select(BreakSlot)
        .where(BreakSlot.break_group_id == group_id)
        .order_by(BreakSlot.start_time)
    )
    return [BreakSlotRead.from_orm_slot(s) for s in result.scalars().all()]


@router.post("/{group_id}/slots", response_model=BreakSlotRead, status_code=201)
async def create_slot(group_id: uuid.UUID, body: BreakSlotCreate,
                      db: AsyncSession = Depends(get_db)):
    company_id = _company_id()
    await _get_group(group_id, company_id, db)
    slot = BreakSlot(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        break_group_id=group_id,
        label=body.label,
        break_type=body.break_type,
        start_time=_parse_time(body.start_time, "start_time"),
        end_time=_parse_time(body.end_time, "end_time"),
        duration_minutes=body.duration_minutes,
        max_concurrent=body.max_concurrent,
    )
    db.add(slot)
    await db.commit()
    await db.refresh(slot)
    return BreakSlotRead.from_orm_slot(slot)


@router.delete("/{group_id}/slots/{slot_id}", status_code=204)
async def delete_slot(group_id: uuid.UUID, slot_id: uuid.UUID,
                      db: AsyncSession = Depends(get_db)):
    company_id = _company_id()
    result = await db.execute(
        select(BreakSlot).where(BreakSlot.id == slot_id,
                                BreakSlot.break_group_id == group_id,
                                BreakSlot.company_id == company_id)
    )
    slot = result.scalars().first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    await db.delete(slot)
    await db.commit()
