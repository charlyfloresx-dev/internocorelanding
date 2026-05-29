import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, ConfigDict, Field

from common.infrastructure.database import get_db
from common.context import request_context
from mes_app.models.facility import Facility
from mes_app.models.production_area import ProductionArea
from mes_app.models.resource import Resource
from mes_app.models.resource_support_member import ResourceSupportMember
from mes_app.models.shift_break import ShiftBreak
from mes_app.models.shift import Shift

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class FacilityRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    location_description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class FacilityCreate(BaseModel):
    code: str = Field(max_length=25)
    name: str = Field(max_length=100)
    location_description: Optional[str] = Field(None, max_length=250)


class ProductionAreaRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    facility_id: Optional[uuid.UUID] = None
    model_config = ConfigDict(from_attributes=True)


class ProductionAreaCreate(BaseModel):
    name: str = Field(max_length=100)
    description: Optional[str] = Field(None, max_length=250)
    facility_id: Optional[uuid.UUID] = None


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


class SupportMemberRead(BaseModel):
    id: uuid.UUID
    collaborator_id: uuid.UUID
    role: str
    model_config = ConfigDict(from_attributes=True)


class ResourceRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    resource_type: Optional[str] = None
    capacity: Optional[Decimal] = None
    warehouse_id: Optional[uuid.UUID] = None
    production_area_id: Optional[uuid.UUID] = None
    active: bool
    support_members: List[SupportMemberRead] = []
    model_config = ConfigDict(from_attributes=True)


class ResourceCreate(BaseModel):
    code: str = Field(max_length=13)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(None, max_length=250)
    resource_type: Optional[str] = Field(None, pattern="^(CELL|MACHINE|AREA|LINE)$")
    capacity: Optional[Decimal] = None
    warehouse_id: Optional[uuid.UUID] = None
    production_area_id: Optional[uuid.UUID] = None


class ResourceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=250)
    resource_type: Optional[str] = Field(None, pattern="^(CELL|MACHINE|AREA|LINE)$")
    capacity: Optional[Decimal] = None
    warehouse_id: Optional[uuid.UUID] = None
    production_area_id: Optional[uuid.UUID] = None
    active: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _company_id() -> uuid.UUID:
    ctx = request_context.get()
    if not ctx or not ctx.company_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Valid company context required")
    return ctx.company_id


# ── Facility endpoints ────────────────────────────────────────────────────────

@router.get("/facilities", response_model=List[FacilityRead], tags=["Facilities"])
async def list_facilities(
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    result = await db.execute(
        select(Facility).where(Facility.company_id == company_id, Facility.is_active == True)
    )
    return result.scalars().all()


@router.post("/facilities", response_model=FacilityRead, status_code=status.HTTP_201_CREATED,
             tags=["Facilities"])
async def create_facility(
    body: FacilityCreate,
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    facility = Facility(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        **body.model_dump(),
    )
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    return facility


# ── ProductionArea endpoints ──────────────────────────────────────────────────

@router.get("/production-areas", response_model=List[ProductionAreaRead], tags=["Production Areas"])
async def list_production_areas(
    facility_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    q = select(ProductionArea).where(
        ProductionArea.company_id == company_id,
        ProductionArea.is_active == True,
    )
    if facility_id:
        q = q.where(ProductionArea.facility_id == facility_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/production-areas", response_model=ProductionAreaRead,
             status_code=status.HTTP_201_CREATED, tags=["Production Areas"])
async def create_production_area(
    body: ProductionAreaCreate,
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    area = ProductionArea(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        **body.model_dump(),
    )
    db.add(area)
    await db.commit()
    await db.refresh(area)
    return area


# ── Resource endpoints ────────────────────────────────────────────────────────

@router.get("/", response_model=List[ResourceRead], tags=["Resources"])
async def list_resources(
    resource_type: Optional[str] = None,
    production_area_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    q = (
        select(Resource)
        .options(selectinload(Resource.support_members))
        .where(Resource.company_id == company_id, Resource.active == True)
    )
    if resource_type:
        q = q.where(Resource.resource_type == resource_type)
    if production_area_id:
        q = q.where(Resource.production_area_id == production_area_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{code}", response_model=ResourceRead, tags=["Resources"])
async def get_resource(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    result = await db.execute(
        select(Resource)
        .options(selectinload(Resource.support_members))
        .where(Resource.company_id == company_id, Resource.code == code)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource '{code}' not found")
    return resource


@router.post("/", response_model=ResourceRead, status_code=status.HTTP_201_CREATED,
             tags=["Resources"])
async def create_resource(
    body: ResourceCreate,
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    resource = Resource(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        **body.model_dump(),
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.patch("/{code}", response_model=ResourceRead, tags=["Resources"])
async def update_resource(
    code: str,
    body: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    company_id = _company_id()
    result = await db.execute(
        select(Resource).where(Resource.company_id == company_id, Resource.code == code)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail=f"Resource '{code}' not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)
    await db.commit()
    await db.refresh(resource)
    return resource
