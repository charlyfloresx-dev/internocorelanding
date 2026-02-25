import uuid
from typing import List, Optional
from pydantic import BaseModel

class TokenPayload(BaseModel):
    """
    Schema centralizado para el payload del JWT en InternoCore.
    Asegura consistencia entre Auth, Subscription y Microservicios.
    """
    sub: uuid.UUID # User ID
    company_id: uuid.UUID
    role: str = "OPERATOR" # OWNER, ADMIN, OPERATOR
    role_names: List[str] = [] # Legacy compatibility
    scopes: List[str] = []
    accessible_warehouses: List[uuid.UUID] = [] # RBAC por sucursal
    
    # Nuevos Claims de Suscripción (Enterprise-Ready)
    modules: List[str] = ["auth_core", "inventory_core"]
    status: str = "TRIAL"
    readonly: bool = False
    correlation_id: Optional[str] = None
