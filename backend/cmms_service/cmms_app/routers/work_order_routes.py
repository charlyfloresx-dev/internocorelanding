"""WorkOrder Router — Correctivo, Preventivo y escalación desde Tickets."""
import uuid
import random
import string
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from common.infrastructure.database import get_db
from common.dependencies import get_current_company_id
from common.responses import success_response
from cmms_app.models import WorkOrder, Asset, ToolAssignment
from cmms_app.schemas import WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse
from cmms_app.core.constants import WorkOrderStatus

router = APIRouter(tags=["Work Orders"])


def _generate_reference_code(prefix: str = "OT") -> str:
    """Generates a human-readable folio: OT-2026-A4K2"""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{datetime.now(timezone.utc).year}-{suffix}"


# ── GET /work-orders ──────────────────────────────────────────────────────────
@router.get("/")
async def list_work_orders(
    asset_id: Optional[uuid.UUID] = None,
    wo_status: Optional[WorkOrderStatus] = None,
    assigned_to: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """Unified order list — Kanban / Calendar feed. Filtered by company_id."""
    filters = [WorkOrder.company_id == company_id, WorkOrder.is_active == True]
    if asset_id:
        filters.append(WorkOrder.asset_id == asset_id)
    if wo_status:
        filters.append(WorkOrder.status == wo_status)
    if assigned_to:
        filters.append(WorkOrder.assigned_technician_id == assigned_to)

    result = await db.execute(
        select(WorkOrder).where(and_(*filters)).order_by(WorkOrder.scheduled_start.asc())
    )
    orders = result.scalars().all()
    return success_response(data=[WorkOrderResponse.model_validate(o).model_dump() for o in orders])


# ── POST /work-orders ─────────────────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_work_order(
    payload: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """
    CreateWorkOrder Command:
    1. Validates asset belongs to this company.
    2. Snapshots required tools (inventory_item_id + name).
    3. Links to source_ticket_id if this is an escalation from Tickets Service.
    NOTE: Actual INTERNAL_LOAN transaction to Inventory Service is dispatched
          async via domain event when technician does the physical check-out.
    """
    # Validate asset belongs to company (multitenancy guard)
    asset_result = await db.execute(
        select(Asset).where(
            Asset.id == payload.asset_id,
            Asset.company_id == company_id,
            Asset.is_active == True,
        )
    )
    if not asset_result.scalar_one_or_none():
        raise HTTPException(404, "Asset not found in this company.")

    tools_snapshot = None
    if payload.tools_required:
        tools_snapshot = [
            {"inventory_item_id": str(t.tool_id), "name": t.name}
            for t in payload.tools_required
        ]

    wo = WorkOrder(
        reference_code=_generate_reference_code(),
        asset_id=payload.asset_id,
        maintenance_plan_id=payload.maintenance_plan_id,
        maintenance_type=payload.maintenance_type,
        priority=payload.priority,
        title=payload.title,
        description=payload.description,
        assigned_technician_id=payload.assigned_technician_id,
        supervisor_id=payload.supervisor_id,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
        source_ticket_id=payload.source_ticket_id,
        tools_snapshot=tools_snapshot,
        company_id=company_id,
        tenant_id=company_id,
    )
    db.add(wo)
    await db.commit()
    await db.refresh(wo)
    return success_response(
        data=WorkOrderResponse.model_validate(wo).model_dump(),
        message="Work order created.",
    )


# ── GET /work-orders/{wo_id} ──────────────────────────────────────────────────
@router.get("/{wo_id}")
async def get_work_order(
    wo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    wo = await _get_wo_or_404(db, wo_id, company_id)
    return success_response(data=WorkOrderResponse.model_validate(wo).model_dump())


# ── PATCH /work-orders/{wo_id} ────────────────────────────────────────────────
@router.patch("/{wo_id}")
async def update_work_order(
    wo_id: uuid.UUID,
    payload: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """
    Kanban state machine:
    - COMPLETED transition is blocked if there are open ToolAssignments (not returned).
    """
    wo = await _get_wo_or_404(db, wo_id, company_id)

    # Guard: cannot close if tools are still checked out
    if payload.status == WorkOrderStatus.COMPLETED:
        open_assignments = await db.execute(
            select(ToolAssignment).where(
                ToolAssignment.work_order_id == wo_id,
                ToolAssignment.returned_at.is_(None),
            )
        )
        if open_assignments.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot complete work order: there are tools pending return.",
            )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(wo, field, value)

    db.add(wo)
    await db.commit()
    await db.refresh(wo)
    return success_response(data=WorkOrderResponse.model_validate(wo).model_dump())


# ── GET /work-orders/{wo_id}/pending-tools ────────────────────────────────────
@router.get("/{wo_id}/pending-tools")
async def get_pending_tools(
    wo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """Returns open ToolAssignments blocking WO completion."""
    await _get_wo_or_404(db, wo_id, company_id)
    result = await db.execute(
        select(ToolAssignment).where(
            ToolAssignment.work_order_id == wo_id,
            ToolAssignment.company_id == company_id,
            ToolAssignment.returned_at.is_(None),
        )
    )
    assignments = result.scalars().all()
    return success_response(data=[str(a.tool_id) for a in assignments])


# ── Helper ────────────────────────────────────────────────────────────────────
async def _get_wo_or_404(db: AsyncSession, wo_id: uuid.UUID, company_id: uuid.UUID) -> WorkOrder:
    result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.id == wo_id,
            WorkOrder.company_id == company_id,
            WorkOrder.is_active == True,
        )
    )
    wo = result.scalar_one_or_none()
    if not wo:
        raise HTTPException(404, "Work order not found.")
    return wo
