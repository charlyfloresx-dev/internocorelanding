import uuid
from typing import List, Optional, Union
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
    sub: Union[uuid.UUID, str] = Field(..., validation_alias=AliasChoices("sub", "user_id"), description="ID de usuario (JWT standard 'sub')")
    company_id: Optional[Union[uuid.UUID, str]] = Field(None, validation_alias=AliasChoices("company_id", "cid"), description="ID de la empresa/tenant principal")
    group_id: Optional[Union[uuid.UUID, str]] = Field(None, description="ID del grupo empresarial al que pertenece la empresa")
    role: str = Field("OPERATOR", validation_alias=AliasChoices("role", "role_name"), description="Rol principal (OWNER, ADMIN, OPERATOR)")
    role_names: List[str] = Field([], validation_alias=AliasChoices("role_names", "roles"), description="Lista extendida de nombres de roles")
    scopes: List[str] = Field([], description="Permisos granulares (permissions)")
    accessible_warehouses: List[Union[uuid.UUID, str]] = Field([], description="Lista de almacenes permitidos (RBAC geográfico)")
    
    # --- Industrial Identity (Phase 37: HR Microservice) ---
    wid: Optional[Union[uuid.UUID, str]] = Field(None, validation_alias=AliasChoices("wid", "home_warehouse_id"), description="Almacén base del colaborador (Warehouse Lock)")
    is_supervisor: bool = Field(False, description="Bypass del Warehouse Lock si es true")
    
    # Claims de Suscripción y Gobernanza
    modules: List[str] = Field(["auth_core", "inventory_core"], description="Módulos habilitados por suscripción")
    status: str = Field("TRIAL", description="Estado de suscripción (TRIAL, ACTIVE, PAST_DUE, EXPIRED)")
    readonly: bool = Field(False, description="Si es true, el sistema entra en modo Solo Lectura")
    correlation_id: Optional[str] = Field(None, description="ID de correlación para trazabilidad forense")
    full_name: Optional[str] = Field(None, description="Nombre completo del sujeto (para hidratación de UI)")
    token: Optional[str] = Field(None, description="Token crudo para propagación entre servicios")
    jti: Optional[str] = Field(None, description="JWT ID — usado para revocación server-side de sesiones GOD MODE")
    god_mode: bool = Field(False, description="True si el token proviene de /elevate (break-glass)")

    model_config = ConfigDict(
        extra="ignore", 
        populate_by_name=True,
        str_strip_whitespace=True
    )

    @property
    def user_id(self) -> Union[uuid.UUID, str]:
        """Alias para acceso semántico al ID de usuario."""
        return self.sub
