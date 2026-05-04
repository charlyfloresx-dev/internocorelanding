"""
Pydantic Schemas — Tools & ToolAssignments
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from cmms_app.core.constants import ToolStatus, ToolCondition


class ToolCreate(BaseModel):
    internal_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    current_warehouse_id: uuid.UUID
    is_calibratable: bool = False
    last_calibration_date: Optional[datetime] = None
    next_calibration_date: Optional[datetime] = None


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ToolStatus] = None
    condition: Optional[ToolCondition] = None
    current_warehouse_id: Optional[uuid.UUID] = None
    last_calibration_date: Optional[datetime] = None
    next_calibration_date: Optional[datetime] = None
    calibration_certificate: Optional[str] = None


class ToolResponse(BaseModel):
    id: uuid.UUID
    internal_code: str
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    status: ToolStatus
    condition: ToolCondition
    current_warehouse_id: uuid.UUID
    is_calibratable: bool
    last_calibration_date: Optional[datetime] = None
    next_calibration_date: Optional[datetime] = None
    qr_token: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Check-out / Check-in ──────────────────────────────────────────────────────

class ToolCheckOutRequest(BaseModel):
    work_order_id: uuid.UUID
    technician_id: uuid.UUID
    expected_return_at: Optional[datetime] = None
    checkout_condition: ToolCondition = ToolCondition.GOOD


class ToolCheckInRequest(BaseModel):
    return_condition: ToolCondition
    return_notes: Optional[str] = None
    signature_file_path: Optional[str] = None


class ToolAssignmentResponse(BaseModel):
    id: uuid.UUID
    tool_id: uuid.UUID
    work_order_id: uuid.UUID
    technician_id: uuid.UUID
    checked_out_at: datetime
    expected_return_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    checkout_condition: ToolCondition
    return_condition: Optional[ToolCondition] = None
    return_notes: Optional[str] = None

    model_config = {"from_attributes": True}
