from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class InvitationBase(BaseModel):
    email: EmailStr
    role_id: UUID

class InvitationCreate(InvitationBase):
    pass

class InvitationResponse(InvitationBase):
    id: UUID
    code: str
    company_id: UUID
    expires_at: datetime
    is_used: bool

    class Config:
        from_attributes = True

class UserRegistration(BaseModel):
    code: str = Field(..., min_length=8, max_length=8)
    password: str = Field(..., min_length=6)
    full_name: str

class UserRoleAssignment(BaseModel):
    email: EmailStr
    role_id: UUID
