import uuid
from typing import List, Optional

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

# Asumimos que la configuración se importa desde un módulo central
# from app.core.config import settings

# --- Mock de settings para demostración ---
class MockSettings:
    SECRET_KEY: str = "a_very_secret_key_that_should_be_in_env"
    ALGORITHM: str = "HS256"

settings = MockSettings()
# -----------------------------------------

# Esquema de seguridad para obtener el token desde el header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Schemas de Seguridad ---

class TokenPayload(BaseModel):
    """
    Define el payload esperado dentro del JWT.
    'sub' es el estándar para el ID de usuario.
    """
    sub: uuid.UUID
    company_id: uuid.UUID
    scopes: List[str] = []

class SecurityContext(BaseModel):
    """
    Objeto inyectado en los endpoints protegidos con el contexto del tenant y usuario.
    """
    user_id: uuid.UUID
    company_id: uuid.UUID
    scopes: List[str]

# --- Dependencias de Seguridad ---

async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    Decodifica y valida el access_token, retornando el payload si es válido.
    Esta es la primera capa de validación (firma y expiración del token).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # El payload del token se valida contra el schema Pydantic
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    return token_data

async def get_current_tenant_context(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    payload: TokenPayload = Depends(get_current_user_payload)
) -> SecurityContext:
    """
    Implementa la "Doble Validación" de multitenencia.
    1. Valida que el header X-Company-ID exista.
    2. Compara el X-Company-ID del header con el company_id del JWT.
    3. Si todo es correcto, retorna el contexto de seguridad.
    """
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-ID header is missing",
        )

    try:
        header_company_id = uuid.UUID(x_company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Company-ID format. Must be a valid UUID.",
        )

    if header_company_id != payload.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant Mismatch: Header company does not match token.",
        )

    return SecurityContext(
        user_id=payload.sub,
        company_id=payload.company_id,
        scopes=payload.scopes
    )

def require_scope(required_scopes: List[str]):
    """
    Factory de dependencias para validar scopes.
    Crea una dependencia que verifica si el usuario tiene todos los scopes requeridos.
    """
    def _require_scope(
        context: SecurityContext = Depends(get_current_tenant_context)
    ) -> SecurityContext:
        user_scopes = set(context.scopes)
        for scope in required_scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Requires scope: '{scope}'",
                )
        return context
    
    return _require_scope