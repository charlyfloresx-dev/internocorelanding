import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, AliasChoices

class TokenPayload(BaseModel):
    """
    Schema centralizado para el payload del JWT en InternoCore (SSOT).
    
    Flujo de Denegación de Seguridad:
    1. Identidad: El sub/user_id identifica al sujeto.
    2. Entitlements: modules define qué microservicios puede acceder.
    3. Gobernanza: readonly bloquea mutaciones (402).
    4. Kill Switch: status != 'EXPIRED' permite sesión.
    """
    sub: uuid.UUID = Field(..., validation_alias=AliasChoices("sub", "user_id"), description="ID de usuario (JWT standard 'sub')")
    company_id: uuid.UUID = Field(..., description="ID de la empresa/tenant principal")
    group_id: Optional[uuid.UUID] = Field(None, description="ID del grupo empresarial al que pertenece la empresa")
    role: str = Field("OPERATOR", description="Rol principal (OWNER, ADMIN, OPERATOR)")
    role_names: List[str] = Field([], description="Lista extendida de nombres de roles")
    scopes: List[str] = Field([], description="Permisos granulares (permissions)")
    accessible_warehouses: List[uuid.UUID] = Field([], description="Lista de almacenes permitidos (RBAC geográfico)")
    
    # Claims de Suscripción y Gobernanza
    modules: List[str] = Field(["auth_core", "inventory_core"], description="Módulos habilitados por suscripción")
    status: str = Field("TRIAL", description="Estado de suscripción (TRIAL, ACTIVE, PAST_DUE, EXPIRED)")
    readonly: bool = Field(False, description="Si es true, el sistema entra en modo Solo Lectura")
    correlation_id: Optional[str] = Field(None, description="ID de correlación para trazabilidad forense")
    token: Optional[str] = Field(None, description="Token crudo para propagación entre servicios")

    model_config = ConfigDict(
        extra="ignore", 
        populate_by_name=True,
        str_strip_whitespace=True
    )

    @property
    def user_id(self) -> uuid.UUID:
        """Alias para acceso semántico al ID de usuario."""
        return self.sub
