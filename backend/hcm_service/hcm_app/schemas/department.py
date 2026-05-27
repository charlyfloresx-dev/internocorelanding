import uuid
from typing import Optional
from pydantic import BaseModel, Field

class DepartmentRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

class DepartmentCreate(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    description: Optional[str] = Field(None, max_length=250)
    is_active: bool = True

class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=250)
    is_active: Optional[bool] = None
