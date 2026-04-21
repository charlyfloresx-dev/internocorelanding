from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class UserCompanyRoleBase(BaseModel):
    # CORRECCIÓN: Tipos UUID en lugar de int
    user_id: UUID
    company_id: UUID
    # CORRECCIÓN: Se cambia 'role' (str) a 'role_id' (UUID)
    role_id: UUID 

class UserCompanyRoleCreate(UserCompanyRoleBase):
    is_new: bool = True # Default to True for creation

class UserCompanyRoleResponse(UserCompanyRoleBase):
    is_new: bool # Include in response
    model_config = ConfigDict(from_attributes=True)

class UserCompanyRoleUpdate(BaseModel):
    # CORRECCIÓN: Permitir actualizar el UUID del rol
    role_id: Optional[UUID] = None 
    is_new: Optional[bool] = None # Allow updating is_new
