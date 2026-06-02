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
import traceback

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
    material_status: Optional[str] = None
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
    material_status: Optional[str] = None
    bom_lines_created: Optional[int] = None
    message: Optional[str] = None
    timestamp: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[WorkOrderRead],
    dependencies=[Depends(require_scope(["mes:read"]))],
)
async def get_work_orders(
    status: Optional[str] = None,
    wo_type: Optional[WOType] = None,
    item_code: Optional[str] = None,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Lista órdenes activas de la compañía con filtros opcionales."""
    query = select(WorkOrder).where(WorkOrder.company_id == company_id)
    if status:
        query = query.where(WorkOrder.status == status)
    if wo_type:
        query = query.where(WorkOrder.wo_type == wo_type)
    if item_code:
        query = query.where(WorkOrder.item_code == item_code)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get(
    "/types",
    response_model=List[dict],
    dependencies=[Depends(require_scope(["mes:read"]))],
    summary="Lista los tipos de OT disponibles",
)
async def get_work_order_types():
    """Returns configurable WO type catalog from server enum — not hardcoded on client."""
    labels = {
        "STANDARD":          "Estándar",
        "NON_STANDARD":      "No Estándar",
        "REPAIR":            "Reparación",
        "REWORK":            "Retrabajo",
        "TEST":              "Prototipo / Prueba",
        "TOOLING":           "Herramental",
        "SCRAP_REPLACEMENT": "Reposición por Scrap",
    }
    return [
        {"value": t.value, "label": labels.get(t.value, t.value)}
        for t in WOType
    ]


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
    Crea OT con PLANNED_OUTPUT únicamente.
    El material se surte por separado via POST /{number}/issue-material.
    material_status="PENDING_ISSUE" genera alerta en UI sin bloquear el flujo.
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


class BulkWorkOrderItem(BaseModel):
    order_number: str = Field(description="ERP order code — skipped if already exists")
    item_code: str
    order_qty: int = Field(ge=1)
    due_date: datetime
    alias: Optional[str] = None
    wo_type: Optional[WOType] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class BulkWorkOrderResponse(BaseModel):
    created: int
    skipped: int
    errors: List[dict] = Field(default_factory=list)


@router.post(
    "/bulk",
    response_model=BulkWorkOrderResponse,
    status_code=201,
    dependencies=[Depends(require_scope(["mes:write"]))],
    summary="Crear múltiples OTs de una sola llamada (importación CSV)",
)
async def bulk_create_work_orders(
    items: List[BulkWorkOrderItem],
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Acepta un array JSON de OTs. Duplicados (mismo order_number para la empresa)
    son omitidos sin error. Retorna contadores created/skipped/errors.
    """
    created = 0
    skipped = 0
    errors: list[dict] = []

    for idx, item in enumerate(items):
        try:
            existing = await db.execute(
                select(WorkOrder.id).where(
                    WorkOrder.order_number == item.order_number,
                    WorkOrder.company_id == company_id,
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            handler = WorkOrderHandler(db)
            cmd = CreateWorkOrderCommand(
                order_number=item.order_number,
                item_code=item.item_code,
                order_qty=item.order_qty,
                due_date=item.due_date,
                company_id=company_id,
                alias=item.alias,
                wo_type=item.wo_type,
            )
            await handler.handle_create(cmd)
            await db.flush()
            created += 1
        except Exception as exc:
            await db.rollback()
            errors.append({
                "row": idx,
                "order_number": item.order_number,
                "error": str(exc),
            })

    if created:
        await db.commit()

    return BulkWorkOrderResponse(created=created, skipped=skipped, errors=errors)


@router.post(
    "/{order_number}/issue-material",
    response_model=CommandResponse,
    dependencies=[Depends(require_scope(["mes:write"]))],
    summary="Surtir material a la OT (explotar BOM → MATERIAL_INPUT lines)",
)
async def issue_material(
    order_number: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """
    Paso de surtido: explota el BOM de inventario y crea las líneas MATERIAL_INPUT.
    Idempotente — si ya fue surtida, retorna sin cambios.
    """
    handler = WorkOrderHandler(db)
    return await handler.handle_issue_material(order_number, company_id)


class WorkOrderUpdate(BaseModel):
    alias: Optional[str] = None
    request_date: Optional[datetime] = None
    wo_type: Optional[WOType] = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


@router.put(
    "/{order_number}",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def update_work_order(
    order_number: str,
    request: WorkOrderUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza campos editables de la Orden de Trabajo."""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.order_number == order_number,
            WorkOrder.company_id == company_id,
        )
    )
    wo = result.scalar_one_or_none()
    if not wo:
        raise NotFoundException("WorkOrder not found")

    if request.alias is not None:
        wo.alias = request.alias
    if request.request_date is not None:
        wo.request_date = request.request_date
    if request.wo_type is not None:
        wo.wo_type = request.wo_type

    await db.commit()
    await db.refresh(wo)
    return wo


@router.patch(
    "/{order_number}/release",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def release_work_order(
    order_number: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Libera una Orden de Trabajo (Transición DRAFT -> RELEASED)."""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.order_number == order_number,
            WorkOrder.company_id == company_id,
        )
    )
    wo = result.scalar_one_or_none()
    if not wo:
        raise NotFoundException("WorkOrder not found")

    if wo.status != "DRAFT":
        from common.exceptions import BusinessRuleException
        raise HTTPException(
            status_code=400,
            detail=f"Cannot release work order in {wo.status} status. Must be DRAFT."
        )

    wo.status = "RELEASED"
    wo.release_date = datetime.now()
    await db.commit()
    await db.refresh(wo)
    return wo


@router.patch(
    "/{order_number}/close",
    response_model=WorkOrderRead,
    dependencies=[Depends(require_scope(["mes:write"]))],
)
async def close_work_order(
    order_number: str,
    company_id: uuid.UUID = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
):
    """Cierra administrativamente una Orden de Trabajo (Transición COMPLETED -> CLOSED)."""
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.order_number == order_number,
            WorkOrder.company_id == company_id,
        )
    )
    wo = result.scalar_one_or_none()
    if not wo:
        raise NotFoundException("WorkOrder not found")

    if wo.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot close work order in {wo.status} status. Must be COMPLETED."
        )

    wo.status = "CLOSED"
    await db.commit()
    await db.refresh(wo)
    return wo
