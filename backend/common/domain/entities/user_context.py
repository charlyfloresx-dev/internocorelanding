import uuid
from pydantic import BaseModel, Field
from typing import Optional, List

class UserContext(BaseModel):
    # Compatibilidad con TokenPayload (JWT standard)
    sub: Optional[str] = Field(None, alias="user_id")
    user_id: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    group_id: Optional[uuid.UUID] = None
    trace_id: Optional[str] = None
    token: Optional[str] = None
    
    # Seguridad e Industrialización
    readonly: bool = False
    scopes: List[str] = []
    status: str = "ACTIVE"
    jti: Optional[str] = None
    god_mode: bool = False
    
    # RBAC & Geographic (Phase 33.5)
    role: str = "OPERATOR"
    role_names: List[str] = []
    accessible_warehouses: List[uuid.UUID] = []

    model_config = {
        "populate_by_name": True
    }
