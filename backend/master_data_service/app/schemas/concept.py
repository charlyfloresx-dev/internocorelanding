from pydantic import BaseModel, Field
from typing import Optional
import uuid

class ConceptBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=250)
    type: str = Field(..., max_length=50) # ENTRY, OUTPUT, TRANSFER, etc
    operation_type: Optional[str] = Field(None, max_length=50)
    requires_external_entity: bool = False
    requires_target_warehouse: bool = False
    is_active: bool = True

class ConceptCreate(ConceptBase):
    pass

class ConceptUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=250)
    type: Optional[str] = Field(None, max_length=50)
    operation_type: Optional[str] = Field(None, max_length=50)
    requires_external_entity: Optional[bool] = None
    requires_target_warehouse: Optional[bool] = None
    is_active: Optional[bool] = None

class ConceptResponse(ConceptBase):
    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
