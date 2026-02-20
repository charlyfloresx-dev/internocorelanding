from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.models.work_order import WorkOrder, Rout, OperationTime
from pydantic import BaseModel
import uuid
from datetime import datetime
from sqlalchemy import select, and_
from typing import List, Optional
from common.exceptions import NotFoundException
from common.responses import ApiResponse

router = APIRouter()

# Schemas
class WorkOrderRead(BaseModel):
    order_number: str
    item_code: str
    order_qty: int
    manufactured_qty: int
    status: str
    due_date: datetime
    
    class Config:
        from_attributes = True

class WorkOrderCreate(BaseModel):
    order_number: str
    item_code: str
    order_qty: int
    due_date: datetime
    company_id: uuid.UUID
    alias: Optional[str] = None

# Endpoints
@router.get("/", response_model=List[WorkOrderRead])
async def get_work_orders(db: AsyncSession = Depends(get_db)):
    """Listado general de órdenes de trabajo."""
    query = select(WorkOrder)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{order_number}", response_model=WorkOrderRead)
async def get_work_order(order_number: str, db: AsyncSession = Depends(get_db)):
    """Detalle de una orden específica."""
    wo = await db.get(WorkOrder, order_number)
    if not wo:
        raise NotFoundException("WorkOrder not found")
    return wo

@router.post("/", response_model=WorkOrderRead)
async def create_work_order(request: WorkOrderCreate, db: AsyncSession = Depends(get_db)):
    """Carga de una nueva orden de trabajo."""
    wo = WorkOrder(
        order_number=request.order_number,
        item_code=request.item_code,
        order_qty=request.order_qty,
        due_date=request.due_date,
        company_id=request.company_id,
        alias=request.alias,
        release_date=datetime.now(),
        status="RELEASED"
    )
    db.add(wo)
    await db.commit()
    await db.refresh(wo)
    return wo
