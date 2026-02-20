from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.models.labor import Labor, LaborType
from pydantic import BaseModel
import uuid
from datetime import datetime
from sqlalchemy import select, update, and_
from typing import List, Optional

from common.exceptions import NotFoundException
from common.responses import ApiResponse

router = APIRouter()

# Schemas
class LaborRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_number: Optional[int]
    clock_in: datetime
    clock_out: Optional[datetime]
    is_active_labor: bool
    
    class Config:
        from_attributes = True

class LaborClockIn(BaseModel):
    resource_result_id: uuid.UUID
    user_id: uuid.UUID
    company_id: uuid.UUID
    employee_number: Optional[int] = None
    type_id: Optional[uuid.UUID] = None

class LaborClockOut(BaseModel):
    resource_result_id: uuid.UUID
    user_id: uuid.UUID

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
async def clock_in(request: LaborClockIn, db: AsyncSession = Depends(get_db)):
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
        company_id=request.company_id,
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
