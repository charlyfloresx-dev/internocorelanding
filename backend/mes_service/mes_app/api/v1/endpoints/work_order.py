from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from mes_app.dependencies import get_db, get_current_company
from mes_app.models.work_order import WorkOrder
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from datetime import datetime
from sqlalchemy import select, and_
from typing import List, Optional, Any
from common.exceptions import NotFoundException
from common.responses import ApiResponse
from common.security.dependencies import require_scope
from mes_app.core.handlers.work_order_handler import WorkOrderHandler, CreateWorkOrderCommand

router = APIRouter()

# Schemas
class WorkOrderRead(BaseModel):
    id: uuid.UUID = Field(description="Unique ID of the work order")
    order_number: str = Field(description="Display order number/folio")
    status: str = Field(description="Order status (PLANNED, ACTIVE, COMPLETED)")
    
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )
    
class CommandResponse(BaseModel):
    id: str
    status: str
    timestamp: str

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
    db: AsyncSession = Depends(get_db),
):
    """Listado de órdenes de la compañía. Filtrado por company_id del JWT."""
    query = select(WorkOrder.id, WorkOrder.order_number, WorkOrder.status).where(
        WorkOrder.company_id == company_id
    )
    result = await db.execute(query)
    records = result.all()
    return [{"id": row.id, "order_number": row.order_number, "status": row.status} for row in records]


@router.get("/{order_number}", response_model=WorkOrderRead, dependencies=[Depends(require_scope(["mes:read"]))])
async def get_work_order(
    order_number: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Detalle de una orden específica buscada por order_number."""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.order_number == order_number,
            WorkOrder.company_id == company_id,
        )
    )
    wo = result.scalar_one_or_none()
    if not wo:
        raise NotFoundException("WorkOrder not found")
    return wo

@router.post("/", response_model=CommandResponse, dependencies=[Depends(require_scope(["mes:write"]))])
async def create_work_order(
    request: WorkOrderCreate, 
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    """Carga de una nueva orden de trabajo."""
    handler = WorkOrderHandler(db)
    cmd = CreateWorkOrderCommand(
        order_number=request.order_number,
        item_code=request.item_code,
        order_qty=request.order_qty,
        due_date=request.due_date,
        company_id=company_id,
        alias=request.alias
    )
    
    # Execute the atomic handler
    response = await handler.handle_create(cmd)
    
    # Ensure root commit after UoW block finishes successfully
    await db.commit()
    return response
