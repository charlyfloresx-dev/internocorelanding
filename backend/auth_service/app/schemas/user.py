from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from typing import Optional
from datetime import datetime

# --- Esquema Base ---
# Contiene los campos comunes para evitar repetición
class UserBase(BaseModel):
    email: EmailStr

# --- Esquema para Creación (POST) ---
# Se usa en el endpoint para registrar nuevos usuarios
class UserCreate(UserBase):
    password: str
    is_active: Optional[bool] = True

# --- Esquema para Actualización (PUT/PATCH) ---
# Todos los campos son opcionales aquí
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

# --- Esquema para Respuesta (Response Model) ---
# Lo que el API devuelve al cliente
class UserResponse(UserBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: Optional[datetime] = None
    
    # Configuración para que Pydantic pueda leer modelos de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

# --- Esquema de Sesión Actual ---
# Utilizado para el endpoint /me o perfiles rápidos
class UserMeResponse(BaseModel):
    id: UUID
    email: EmailStr
    active_company_id: UUID
    
    model_config = ConfigDict(from_attributes=True)