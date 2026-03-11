from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

class CompanyEntity(BaseModel):
    id: UUID
    name: str
    parent_group_id: Optional[UUID] = None
    logo: Optional[str] = None
    status: str

class RoleEntity(BaseModel):
    id: UUID
    name: str
    is_system_role: bool
    company_id: Optional[UUID] = None

class UserCompanyRoleEntity(BaseModel):
    company_id: UUID
    role_names: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)
    is_new: bool = False
    company_name: Optional[str] = None
    group_id: Optional[UUID] = None
    logo: Optional[str] = None

class UserEntity(BaseModel):
    id: UUID
    email: str
    hashed_password: Optional[str] = None
    identity_token: Optional[str] = None
    is_active: bool = True
    company_id: UUID
