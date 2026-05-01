from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.dependencies import get_db, get_current_company
from mes_app.models.labor import Labor, LaborType
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from datetime import datetime
from sqlalchemy import select, update, and_
from typing import List, Optional

from common.exceptions import NotFoundException
from common.responses import ApiResponse

router = APIRouter()

# Schemas
class LaborRead(BaseModel):
    id: uuid.UUID = Field(description="Unique ID of the labor record")
    user_id: uuid.UUID = Field(description="System User ID")
    employee_number: Optional[int] = Field(None, description="External employee ID or number")
    clock_in: datetime = Field(description="Start time of the labor session")
    clock_out: Optional[datetime] = Field(None, description="End time of the labor session")
    is_active_labor: bool = Field(description="Flag indicating if the user is currently clocked in")
    
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

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class LaborClockOut(BaseModel):
    resource_result_id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

# Endpoints
@router.get("/active/{resource_result_id}", response_model=List[LaborRead])
async def get_active_labor(resource_result_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retorna el listado de personal activo en la línea."""
    query = select(Labor).where(
        and_(
            Labor.resource_result_id == resource_result_id,
            Labor.is_active_labor == True
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/history/{resource_result_id}", response_model=List[LaborRead])
async def get_labor_history(resource_result_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Historial completo de labor para el turno."""
    query = select(Labor).where(Labor.resource_result_id == resource_result_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/clock-in")
async def clock_in(
    request: LaborClockIn, 
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    # 1. Verificar si ya está activo
    query = select(Labor).where(
        and_(
            Labor.resource_result_id == request.resource_result_id,
            Labor.user_id == request.user_id,
            Labor.is_active_labor == True
        )
    )
    result = await db.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already clocked in")

    # 2. Registrar entrada
    labor = Labor(
        resource_result_id=request.resource_result_id,
        user_id=request.user_id,
        company_id=company_id,
        employee_number=request.employee_number,
        clock_in=datetime.now(),
        is_active_labor=True,
        type_id=request.type_id
    )
    db.add(labor)
    await db.commit()
    return {"message": "Clock-in successful"}

@router.post("/clock-out")
async def clock_out(request: LaborClockOut, db: AsyncSession = Depends(get_db)):
    # 3. Registrar salida
    query = update(Labor).where(
        and_(
            Labor.resource_result_id == request.resource_result_id,
            Labor.user_id == request.user_id,
            Labor.is_active_labor == True
        )
    ).values(
        clock_out=datetime.now(),
        is_active_labor=False
    )
    result = await db.execute(query)
    await db.commit()
    
    if result.rowcount == 0:
        raise NotFoundException("Active labor record not found")
        
    return {"message": "Clock-out successful"}
