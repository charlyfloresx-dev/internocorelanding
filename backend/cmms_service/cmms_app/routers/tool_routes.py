"""Tool Router — CRUD + Check-out / Check-in (Tool Crib)."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from common.infrastructure.database import get_db
from common.dependencies import get_current_company_id
from common.responses import success_response
from cmms_app.models import Tool, ToolAssignment, WorkOrder
from cmms_app.schemas import (
    ToolCreate, ToolUpdate, ToolResponse,
    ToolCheckOutRequest, ToolCheckInRequest, ToolAssignmentResponse,
)
from cmms_app.core.constants import ToolStatus, WorkOrderStatus
from cmms_app.core.config import settings
from cmms_app.services.storage_service import generate_qr_payload

router = APIRouter(tags=["Tools"])


# ── GET /tools ────────────────────────────────────────────────────────────────
@router.get("/")
async def list_tools(
    warehouse_id: Optional[uuid.UUID] = None,
    tool_status: Optional[ToolStatus] = None,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    filters = [Tool.company_id == company_id, Tool.is_active == True]
    if warehouse_id:
        filters.append(Tool.current_warehouse_id == warehouse_id)
    if tool_status:
        filters.append(Tool.status == tool_status)

    result = await db.execute(select(Tool).where(and_(*filters)))
    tools = result.scalars().all()
    return success_response(data=[ToolResponse.model_validate(t).model_dump() for t in tools])


# ── POST /tools ───────────────────────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tool(
    payload: ToolCreate,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    existing = await db.execute(
        select(Tool).where(
            Tool.company_id == company_id,
            Tool.internal_code == payload.internal_code,
            Tool.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Tool code '{payload.internal_code}' already exists.")

    tool = Tool(**payload.model_dump(), company_id=company_id, tenant_id=company_id)
    tool.generate_qr_token(settings.QR_SIGNING_SECRET)

    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return success_response(data=ToolResponse.model_validate(tool).model_dump(), message="Tool created.")


# ── PATCH /tools/{tool_id} ────────────────────────────────────────────────────
@router.patch("/{tool_id}")
async def update_tool(
    tool_id: uuid.UUID,
    payload: ToolUpdate,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    tool = await _get_tool_or_404(db, tool_id, company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tool, field, value)
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return success_response(data=ToolResponse.model_validate(tool).model_dump())


# ── POST /tools/{tool_id}/checkout ───────────────────────────────────────────
@router.post("/{tool_id}/checkout", status_code=status.HTTP_201_CREATED)
async def checkout_tool(
    tool_id: uuid.UUID,
    payload: ToolCheckOutRequest,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """
    Check-Out Command:
    1. Validates tool is AVAILABLE in this company.
    2. Validates the WorkOrder belongs to the same company.
    3. Creates ToolAssignment and sets tool status to ASSIGNED.
    """
    tool = await _get_tool_or_404(db, tool_id, company_id)

    if tool.status != ToolStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tool is not available. Current status: {tool.status.value}",
        )

    # Validate WorkOrder belongs to same company
    wo_result = await db.execute(
        select(WorkOrder).where(
            WorkOrder.id == payload.work_order_id,
            WorkOrder.company_id == company_id,
        )
    )
    if not wo_result.scalar_one_or_none():
        raise HTTPException(404, "WorkOrder not found in this company.")

    assignment = ToolAssignment(
        tool_id=tool.id,
        work_order_id=payload.work_order_id,
        technician_id=payload.technician_id,
        checked_out_at=datetime.now(timezone.utc),
        expected_return_at=payload.expected_return_at,
        checkout_condition=payload.checkout_condition,
        company_id=company_id,
        tenant_id=company_id,
    )
    tool.status = ToolStatus.ASSIGNED
    db.add(assignment)
    db.add(tool)
    await db.commit()
    await db.refresh(assignment)
    return success_response(
        data=ToolAssignmentResponse.model_validate(assignment).model_dump(),
        message="Tool checked out successfully.",
    )


# ── POST /tools/{tool_id}/checkin ────────────────────────────────────────────
@router.post("/{tool_id}/checkin/{assignment_id}")
async def checkin_tool(
    tool_id: uuid.UUID,
    assignment_id: uuid.UUID,
    payload: ToolCheckInRequest,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """
    Check-In Command:
    1. Closes the ToolAssignment with return condition.
    2. Sets tool back to AVAILABLE (or IN_MAINTENANCE if damaged).
    """
    tool = await _get_tool_or_404(db, tool_id, company_id)

    assign_result = await db.execute(
        select(ToolAssignment).where(
            ToolAssignment.id == assignment_id,
            ToolAssignment.tool_id == tool_id,
            ToolAssignment.company_id == company_id,
        )
    )
    assignment: Optional[ToolAssignment] = assign_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(404, "Assignment not found.")
    if assignment.returned_at is not None:
        raise HTTPException(409, "Tool already returned.")

    assignment.returned_at = datetime.now(timezone.utc)
    assignment.return_condition = payload.return_condition
    assignment.return_notes = payload.return_notes
    assignment.signature_file_path = payload.signature_file_path

    from cmms_app.core.constants import ToolCondition
    tool.status = (
        ToolStatus.IN_MAINTENANCE
        if payload.return_condition == ToolCondition.DAMAGED
        else ToolStatus.AVAILABLE
    )
    tool.condition = payload.return_condition

    db.add(assignment)
    db.add(tool)
    await db.commit()
    await db.refresh(assignment)

    return success_response(
        data=ToolAssignmentResponse.model_validate(assignment).model_dump(),
        message="Tool checked in successfully.",
    )


# ── GET /tools/{tool_id}/qr ───────────────────────────────────────────────────
@router.get("/{tool_id}/qr")
async def get_tool_qr(
    tool_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    tool = await _get_tool_or_404(db, tool_id, company_id)
    qr_url, sig = generate_qr_payload("tools", tool.id)
    return success_response(data={"qr_url": qr_url, "sig": sig, "tool_id": str(tool.id)})


# ── Helper ────────────────────────────────────────────────────────────────────
async def _get_tool_or_404(db: AsyncSession, tool_id: uuid.UUID, company_id: uuid.UUID) -> Tool:
    result = await db.execute(
        select(Tool).where(Tool.id == tool_id, Tool.company_id == company_id, Tool.is_active == True)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(404, "Tool not found.")
    return tool
