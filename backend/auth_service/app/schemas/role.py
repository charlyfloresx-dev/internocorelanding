from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import List, Optional

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    # CORRECCIÓN: Tipo UUID en lugar de int
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class RoleUpdate(RoleBase):
    name: Optional[str] = None