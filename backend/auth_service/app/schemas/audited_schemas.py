from pydantic import BaseModel, Field, EmailStr, UUID4
from typing import List, Optional


class CompanyAccess(BaseModel):
    """
    DTO enriquecido para la respuesta del login.
    Proporciona al frontend el contexto necesario para operar.
    """
    id: UUID4
    name: str
    roles: List[str] = Field(..., description="Lista de roles del usuario en esta compañía.")
    company_status: str = Field(..., description="Estado actual de la compañía (ej: ACTIVE, SUSPENDED).")

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """
    Respuesta del primer paso de autenticación (Handshake).
    """
    selection_token: str
    companies: List[CompanyAccess]


class UserUpdate(BaseModel):
    """
    Esquema para actualizar un usuario.
    El company_id es intencionalmente excluido para garantizar su inmutabilidad.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None


class TenantRegistration(BaseModel):
    """
    DTO para el registro de un nuevo tenant (empresa + usuario admin).
    """
    company_name: str
    admin_email: EmailStr
    admin_password: str
    admin_first_name: str
    admin_last_name: Optional[str] = None