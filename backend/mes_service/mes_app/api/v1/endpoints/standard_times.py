import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict, Field

from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from mes_app.dependencies import get_current_company
from mes_app.models.standard_time import StandardTime

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class StandardTimeRead(BaseModel):
    id: uuid.UUID
    item_code: str
    operation_name: str
    sequence_number: int
    set_time_hours: Decimal
    cycle_time_seconds: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class StandardTimeCreate(BaseModel):
    item_code: str = Field(max_length=100)
    operation_name: str = Field(max_length=100)
    sequence_number: int = Field(10, ge=1, description="Route position (multiples of 10 recommended)")
    set_time_hours: Decimal = Field(gt=0, decimal_places=4)
    cycle_time_seconds: Optional[int] = Field(None, ge=1)


class StandardTimeUpdate(BaseModel):
    operation_name: Optional[str] = Field(None, max_length=100)
    sequence_number: Optional[int] = Field(None, ge=1)
    set_time_hours: Optional[Decimal] = Field(None, gt=0, decimal_places=4)
    cycle_time_seconds: Optional[int] = Field(None, ge=1)


class BulkCreateRequest(BaseModel):
    items: List[StandardTimeCreate]


class BulkCreateResponse(BaseModel):
    created: int
    skipped: int
    errors: List[dict] = Field(default_factory=list)


# ── GET / ─────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[StandardTimeRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def list_standard_times(
    item_code: Optional[str] = Query(None, description="Filter by item code"),
    limit: int = Query(200, le=500),
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    q = select(StandardTime).where(StandardTime.company_id == company_id)
    if item_code:
        q = q.where(StandardTime.item_code == item_code)
    q = q.order_by(StandardTime.item_code, StandardTime.sequence_number).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


# ── GET /route/{item_code} — manufacturing route for one item ─────────────────

@router.get(
    "/route/{item_code}",
    response_model=List[StandardTimeRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
    summary="Manufacturing route for an item",
)
async def get_item_route(
    item_code: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Returns all operations for an item ordered by sequence_number (the manufacturing route)."""
    q = (
        select(StandardTime)
        .where(
            StandardTime.company_id == company_id,
            StandardTime.item_code == item_code,
        )
        .order_by(StandardTime.sequence_number)
    )
    result = await db.execute(q)
    return result.scalars().all()


# ── POST / ────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=StandardTimeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def create_standard_time(
    payload: StandardTimeCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    st = StandardTime(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        item_code=payload.item_code,
        operation_name=payload.operation_name,
        sequence_number=payload.sequence_number,
        set_time_hours=payload.set_time_hours,
        cycle_time_seconds=payload.cycle_time_seconds,
    )
    db.add(st)
    await db.commit()
    await db.refresh(st)
    return st


# ── POST /bulk ────────────────────────────────────────────────────────────────

@router.post(
    "/bulk",
    response_model=BulkCreateResponse,
    status_code=status.HTTP_207_MULTI_STATUS,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def bulk_create_standard_times(
    payload: BulkCreateRequest,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    created = 0
    skipped = 0
    errors: list[dict] = []

    for idx, item in enumerate(payload.items):
        try:
            st = StandardTime(
                id=uuid.uuid4(),
                company_id=company_id,
                tenant_id=company_id,
                item_code=item.item_code,
                operation_name=item.operation_name,
                sequence_number=item.sequence_number,
                set_time_hours=item.set_time_hours,
                cycle_time_seconds=item.cycle_time_seconds,
            )
            db.add(st)
            await db.flush()
            created += 1
        except Exception as exc:
            await db.rollback()
            errors.append({"row": idx, "item_code": item.item_code, "error": str(exc)})
            skipped += 1

    if created:
        await db.commit()
    return BulkCreateResponse(created=created, skipped=skipped, errors=errors)


# ── PATCH /{id} ───────────────────────────────────────────────────────────────

@router.patch(
    "/{st_id}",
    response_model=StandardTimeRead,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def update_standard_time(
    st_id: uuid.UUID,
    payload: StandardTimeUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StandardTime).where(
            StandardTime.id == st_id,
            StandardTime.company_id == company_id,
        )
    )
    st = result.scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=404, detail="StandardTime not found")

    if payload.operation_name is not None:
        st.operation_name = payload.operation_name
    if payload.sequence_number is not None:
        st.sequence_number = payload.sequence_number
    if payload.set_time_hours is not None:
        st.set_time_hours = payload.set_time_hours
    if payload.cycle_time_seconds is not None:
        st.cycle_time_seconds = payload.cycle_time_seconds

    await db.commit()
    await db.refresh(st)
    return st


# ── DELETE /{id} ──────────────────────────────────────────────────────────────

@router.delete(
    "/{st_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def delete_standard_time(
    st_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StandardTime).where(
            StandardTime.id == st_id,
            StandardTime.company_id == company_id,
        )
    )
    st = result.scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=404, detail="StandardTime not found")

    await db.delete(st)
    await db.commit()
