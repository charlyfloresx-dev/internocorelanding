from datetime import date
from typing import Optional
import uuid
from pydantic import BaseModel, Field, field_validator


class PlanningEntry(BaseModel):
    work_order_id: uuid.UUID = Field(description="WorkOrder to schedule")
    resource_id: uuid.UUID = Field(description="Production resource (machine/line)")
    shift_id: uuid.UUID = Field(description="Shift for this run")
    date: date = Field(description="Production date (cannot be in the past)")
    planned_quantity: int = Field(gt=0, description="Units planned for this run")

    @field_validator("date")
    @classmethod
    def date_not_in_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Planning date cannot be in the past")
        return v


class BulkLoadResponse(BaseModel):
    scheduled: int = Field(description="Number of production runs successfully created")
    skipped: int = Field(description="Number of entries skipped due to conflicts")
    errors: list[dict] = Field(default_factory=list, description="Validation and conflict details")
