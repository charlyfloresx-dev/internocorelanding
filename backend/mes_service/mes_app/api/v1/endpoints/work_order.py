from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.dependencies import get_db, get_current_company
from mes_app.models.work_order import WorkOrder
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from datetime import datetime
from sqlalchemy import select, and_
from typing import List, Optional
from common.exceptions import NotFoundException
from common.responses import ApiResponse
from common.security.dependencies import require_scope

router = APIRouter()

# Schemas
class WorkOrderRead(BaseModel):
    id: uuid.UUID = Field(description="Unique ID of the work order")
    order_number: str = Field(description="Display order number/folio")
    sku: str = Field(description="Product SKU associated with the order")
    target_qty: float = Field(description="Goal quantity to produce")
    produced_qty: float = Field(description="Actual quantity produced so far")
    status: str = Field(description="Order status (PLANNED, ACTIVE, COMPLETED)")
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )

class WorkOrderCreate(BaseModel):
    order_number: str = Field(description="Order code/id")
    item_code: str = Field(description="Product SKU")
    order_qty: int = Field(description="Total pieces to produce")
    due_date: datetime = Field(description="Promised delivery date")
    alias: Optional[str] = Field(None, description="Internal reference name")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

# Endpoints
@router.get("/", response_model=List[WorkOrderRead], dependencies=[Depends(require_scope(["mes:read"]))])
async def get_work_orders(
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    """Listado de órdenes de la compañía."""
    query = select(WorkOrder).where(WorkOrder.company_id == company_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{order_number}", response_model=WorkOrderRead, dependencies=[Depends(require_scope(["mes:read"]))])
async def get_work_order(order_number: str, db: AsyncSession = Depends(get_db)):
    """Detalle de una orden específica."""
    wo = await db.get(WorkOrder, order_number)
    if not wo:
        raise NotFoundException("WorkOrder not found")
    return wo

@router.post("/", response_model=WorkOrderRead, dependencies=[Depends(require_scope(["mes:write"]))])
async def create_work_order(
    request: WorkOrderCreate, 
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    """Carga de una nueva orden de trabajo."""
    wo = WorkOrder(
        order_number=request.order_number,
        item_code=request.item_code,
        order_qty=request.order_qty,
        due_date=request.due_date,
        company_id=company_id,
        alias=request.alias,
        release_date=datetime.now(),
        status="RELEASED"
    )
    db.add(wo)
    await db.commit()
    await db.refresh(wo)
    return wo
