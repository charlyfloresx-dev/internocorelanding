from pydantic import BaseModel, ConfigDict, Field, EmailStr
from uuid import UUID
from typing import List, Optional

class LoginRequest(BaseModel):
    """Datos de entrada para el login inicial (Soporta Email o RFID)."""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    identity_token: Optional[str] = None

class SelectCompanyRequest(BaseModel):
    company_id: UUID

class CompanySelection(BaseModel):
    """Estructura de cada empresa en la lista de selección."""
    # CORRECCIÓN: Tipo UUID en lugar de str
    company_id: UUID  
    company_name: str
    group_id: Optional[UUID] = None
    group_name: Optional[str] = None
    logo: Optional[str] = None
    role_names: List[str]
    is_new: bool = False # Esencial para el flujo de bienvenida de la demo [cite: 2026-01-27]
    default_tax_rate: float = 0.16

    model_config = ConfigDict(from_attributes=True)

class LoginResponseData(BaseModel):
    selection_token: str
    companies: List[CompanySelection]
    
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
    is_new: bool
    # Base64 encoded QR image for mobile delegation [Phase 94]
    qr_b64: Optional[str] = None
    # Manual IP override for mobile sync [Phase 94]
    base_url: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class UserInfo(BaseModel):
    id: UUID
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True

class AccessTokenResponse(BaseModel):
    """Respuesta final con el JWT de acceso por empresa."""
    access_token: str
    refresh_token: Optional[str] = None   # ← Incluido al seleccionar empresa
    token_type: str = "bearer"
    user_id: UUID
    company_id: UUID
    company_name: Optional[str] = None
    group_id: Optional[UUID] = None
    roles: List[str] = []
    permissions: List[str] = []
    scopes: List[str] = []
    
    # Nested user object for frontend compatibility [Phase 92]
    user: Optional[UserInfo] = None
    
    # Flat fields for legacy support
    user_full_name: Optional[str] = None
    user_email: Optional[str] = None
    
    # Claims de suscripción (Fase 19)
    status: str = "ACTIVE"
    readonly: bool = False
    default_tax_rate: float = 0.16

    model_config = ConfigDict(from_attributes=True)


class RefreshRequest(BaseModel):
    """Cuerpo del endpoint POST /auth/refresh."""
    refresh_token: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterCompanyRequest(BaseModel):
    company_name: str
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str
    group_id: Optional[UUID] = None 
    group_name: Optional[str] = None 

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
