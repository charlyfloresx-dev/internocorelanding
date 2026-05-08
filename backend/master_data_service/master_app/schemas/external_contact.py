from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

class ExternalContactBase(BaseModel):
    full_name: str = Field(..., max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    job_title: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)

class ExternalContactResponse(ExternalContactBase):
    id: uuid.UUID
    company_id: uuid.UUID

    class Config:
        from_attributes = True
