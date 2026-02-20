from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List, Optional

class PermissionBase(BaseModel):
    name: str

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    # CORRECCIÓN: Tipo UUID en lugar de int
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class PermissionUpdate(PermissionBase):
    name: Optional[str] = None