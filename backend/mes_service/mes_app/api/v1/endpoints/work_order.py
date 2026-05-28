from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from mes_app.dependencies import get_db, get_current_company
from mes_app.models.work_order import WorkOrder
from mes_app.models.work_order_line import WorkOrderLine
from mes_app.core.enums import WOType, WorkOrderLineType, WorkOrderLineStatus
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from common.exceptions import NotFoundException
from common.responses import ApiResponse
from common.security.dependencies import require_scope
from mes_app.core.handlers.work_order_handler import WorkOrderHandler, CreateWorkOrderCommand

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class WorkOrderLineRead(BaseModel):
    id: uuid.UUID
    line_number: int
    line_type: WorkOrderLineType
    item_code: str
    item_description: Optional[str] = None
    planned_quantity: Decimal
    actual_quantity: Decimal
    uom: Optional[str] = None
    status: WorkOrderLineStatus
    bom_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class WorkOrderRead(BaseModel):
    id: uuid.UUID
    order_number: str
    item_code: str
    order_quantity: int
    manufactured_quantity: int
    status: str
    wo_type: Optional[WOType] = None
    alias: Optional[str] = None
    request_date: Optional[datetime] = None
    release_date: Optional[datetime] = None
    lines: List[WorkOrderLineRead] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class WorkOrderCreate(BaseModel):
    order_number: str = Field(description="ERP order code")
    item_code: str = Field(description="Product SKU")
    order_qty: int = Field(description="Total pieces to produce")
    due_date: datetime = Field(description="Promised delivery date")
    alias: Optional[str] = Field(None, description="Internal reference name")
    wo_type: Optional[WOType] = Field(None, description="Work order classification")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CommandResponse(BaseModel):
    id: str
    status: str
    timestamp: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[WorkOrderRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_work_orders(
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Lista órdenes activas de la compañía."""
    result = await db.execute(
        select(WorkOrder).where(WorkOrder.company_id == company_id)
    )
    return result.scalars().all()


@router.get(
    "/{order_number}",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_work_order(
    order_number: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Detalle de una orden con sus líneas (BOM + output)."""
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


@router.get(
    "/{order_number}/lines",
    response_model=List[WorkOrderLineRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_work_order_lines(
    order_number: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Líneas de la orden: componentes del BOM (MATERIAL_INPUT) y pieza terminada (PLANNED_OUTPUT)."""
    wo_result = await db.execute(
        select(WorkOrder.id).where(
            WorkOrder.order_number == order_number,
            WorkOrder.company_id == company_id,
        )
    )
    wo_id = wo_result.scalar_one_or_none()
    if not wo_id:
        raise NotFoundException("WorkOrder not found")

    lines_result = await db.execute(
        select(WorkOrderLine)
        .where(
            WorkOrderLine.work_order_id == wo_id,
            WorkOrderLine.company_id == company_id,
        )
        .order_by(WorkOrderLine.line_number)
    )
    return lines_result.scalars().all()


@router.post(
    "/",
    response_model=CommandResponse,
    status_code=201,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def create_work_order(
    request: WorkOrderCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una nueva Orden de Trabajo.

    Automáticamente explota el BOM desde inventory_service y crea líneas
    MATERIAL_INPUT por componente + 1 línea PLANNED_OUTPUT para la pieza terminada.
    Si el BOM no está disponible, crea la orden igualmente (best-effort).
    """
    handler = WorkOrderHandler(db)
    cmd = CreateWorkOrderCommand(
        order_number=request.order_number,
        item_code=request.item_code,
        order_qty=request.order_qty,
        due_date=request.due_date,
        company_id=company_id,
        alias=request.alias,
        wo_type=request.wo_type,
    )
    response = await handler.handle_create(cmd)
    await db.commit()
    return response
