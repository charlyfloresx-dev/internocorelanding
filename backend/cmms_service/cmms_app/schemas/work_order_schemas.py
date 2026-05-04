"""WorkOrderCreate schema updated to include source_ticket_id."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

from pydantic import BaseModel, Field

from cmms_app.core.constants import (
    MaintenanceType, WorkOrderStatus, WorkOrderPriority,
)


class ToolRef(BaseModel):
    tool_id: uuid.UUID       # = inventory_item_id in Inventory Service
    name: str                # denormalized cache for fast reads


class WorkOrderCreate(BaseModel):
    asset_id: uuid.UUID
    maintenance_plan_id: Optional[uuid.UUID] = None
    maintenance_type: MaintenanceType = MaintenanceType.CORRECTIVE
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    assigned_technician_id: Optional[uuid.UUID] = None
    supervisor_id: Optional[uuid.UUID] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    tools_required: Optional[list[ToolRef]] = None

    # Ticket → Maintenance escalation link
    source_ticket_id: Optional[uuid.UUID] = None


class WorkOrderUpdate(BaseModel):
    status: Optional[WorkOrderStatus] = None
    assigned_technician_id: Optional[uuid.UUID] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    root_cause: Optional[str] = None
    resolution_notes: Optional[str] = None
    labor_cost_amount: Optional[Decimal] = None
    parts_cost_amount: Optional[Decimal] = None
    total_cost_amount: Optional[Decimal] = None
    cost_currency: Optional[str] = Field(None, max_length=3)


class WorkOrderResponse(BaseModel):
    id: uuid.UUID
    reference_code: str
    company_id: uuid.UUID
    asset_id: uuid.UUID
    source_ticket_id: Optional[uuid.UUID] = None
    maintenance_type: MaintenanceType
    priority: WorkOrderPriority
    status: WorkOrderStatus
    title: str
    assigned_technician_id: Optional[uuid.UUID] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    tools_snapshot: Optional[Any] = None
    consumables_snapshot: Optional[Any] = None
    total_cost_amount: Optional[Decimal] = None
    cost_currency: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
