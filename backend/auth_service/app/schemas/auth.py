from pydantic import BaseModel, ConfigDict, Field, EmailStr
from uuid import UUID
from typing import List, Optional

class LoginRequest(BaseModel):
    """Datos de entrada para el login inicial."""
    email: EmailStr
    password: str

class CompanySelection(BaseModel):
    """Estructura de cada empresa en la lista de selección."""
    # CORRECCIÓN: Tipo UUID en lugar de str
    company_id: UUID  
    company_name: str
    logo: Optional[str] = None
    role_names: List[str]
    is_new: bool = False # Esencial para el flujo de bienvenida de la demo [cite: 2026-01-27]

    model_config = ConfigDict(from_attributes=True)

class CompanyAccessDto(BaseModel):
    """
    Official DTO for the companies handshaking flow after login.
    """
    selection_token: str
    # CORRECCIÓN: Tipo UUID
    user_id: UUID
    companies: List[CompanySelection]
    # Indicates if the user is new in the global system [cite: 2026-01-27]
    is_new: bool = Field(..., alias="isNew") 

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class AccessTokenResponse(BaseModel):
    """Respuesta final con el JWT de acceso por empresa."""
    access_token: str
    token_type: str = "bearer"
    # CORRECCIÓN: Tipo UUID
    user_id: UUID
    company_id: UUID
    roles: List[str]
    permissions: List[str]
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    """
    Representa los datos contenidos dentro del JWT.
    El 'sub' es el estándar para el ID del usuario.
    """
    sub: Optional[str] = None
    exp: Optional[int] = None