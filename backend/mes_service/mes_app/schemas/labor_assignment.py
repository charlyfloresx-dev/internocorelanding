import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from mes_app.core.enums import LaborRole


class LaborAssignmentCreate(BaseModel):
    collaborator_id: uuid.UUID = Field(..., description="UUID of the collaborator from HCM")
    role: LaborRole = Field(..., description="Role of the collaborator in the shift")


class LaborAssignmentRead(BaseModel):
    id: uuid.UUID
    production_run_id: uuid.UUID
    collaborator_id: uuid.UUID
    role: LaborRole
    shift_id: uuid.UUID
    company_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class BulkAssignRequest(BaseModel):
    production_run_id: uuid.UUID = Field(..., description="Production run to assign collaborators to")
    assignments: List[LaborAssignmentCreate] = Field(default_factory=list, description="List of collaborator assignments")


class BulkAssignResponse(BaseModel):
    assigned: int = Field(..., description="Number of successfully created or updated assignments")
    removed: int = Field(..., description="Number of removed previous assignments")
    warnings: List[str] = Field(default_factory=list, description="Warnings returned during bulk assignment")
