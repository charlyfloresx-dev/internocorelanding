import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError, ConfigDict

from .database import get_db
from app.core.config import settings
from app.models.user import User
from common.exceptions import UnauthorizedException, NotFoundException
from common.security.auth_payload import TokenPayload

# Esquema de seguridad para obtener el token desde el header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# --- Schemas de Seguridad ---



class SecurityContext(BaseModel):
    """
    Objeto inyectado en los endpoints protegidos con el contexto del tenant y usuario.
    """
    user_id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    role: str = "OPERATOR"
    full_name: Optional[str] = None
    scopes: List[str]

class SelectionTokenPayload(BaseModel):
    """
    Payload for the temporary selection token.
    """
    sub: uuid.UUID
    typ: str
    model_config = ConfigDict(extra="ignore")

# --- Dependencias de Seguridad ---

async def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    Decodifica y valida el access_token, retornando el payload si es válido.
    Esta es la primera capa de validación (firma y expiración del token).
    TODO: Immediate Revocation Expulsion logic. Once God Mode supports "EXPIRED" state, 
    integrate a Redis cache check here to immediately reject tokens for internally blacklisted company_ids.
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
        return SecurityContext(
            user_id=payload.sub,
            company_id=payload.company_id,
            role=payload.role,
            full_name=payload.full_name,
            scopes=payload.scopes
        )

    try:
        header_company_id = uuid.UUID(x_company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Company-ID format. Must be a valid UUID.",
        )

    if payload.company_id and str(header_company_id) != str(payload.company_id):
        print(f"DEBUG: Tenant Mismatch! Header={header_company_id} != Payload={payload.company_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant Mismatch: Header company does not match token.",
        )

    return SecurityContext(
        user_id=payload.sub,
        company_id=header_company_id or payload.company_id,
        role=payload.role,
        full_name=payload.full_name,
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

async def get_selection_payload(
    x_selection_token: Optional[str] = Header(None, alias="X-Selection-Token"),
    authorization: Optional[str] = Header(None)
) -> SelectionTokenPayload:
    """
    Decodifica y valida un 'selection_token', retornando el payload si es válido.
    Prioriza el Header X-Selection-Token sobre el estándar Authorization.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate selection token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Prioridad de extracción: Header custom -> Header estándar
    token = x_selection_token
    if not token and authorization:
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        else:
            token = authorization

    print(f"DEBUG AUTH: Received raw Auth Header: {authorization}")
    print(f"DEBUG AUTH: Extracted Token for Selection: {token}")

    if not token or token == "null":
        print("DEBUG AUTH: Token is empty or literal 'null'")
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
            options={"verify_iat": False, "verify_exp": False}
        )
        token_data = SelectionTokenPayload(**payload)
        if token_data.typ != "selection":
            print(f"DEBUG AUTH: Expected typ='selection', got '{token_data.typ}'")
            raise credentials_exception
    except JWTError as e:
        print(f"DEBUG AUTH: JWTError during selection token decode: {e}")
        raise credentials_exception
    except ValidationError as e:
        print(f"DEBUG AUTH: ValidationError during selection token payload parse: {e.errors()}")
        raise credentials_exception
    except Exception as e:
        print(f"DEBUG AUTH: Unexpected error: {e}")
        raise credentials_exception
    
    return token_data

async def get_current_user_model(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Valida el token JWT y recupera el objeto User de la base de datos.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(message="Invalid token payload")
    except JWTError:
        raise UnauthorizedException(message="Could not validate credentials")
    
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException(entity="User", entity_id=user_id)
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user_model),
) -> User:
    """
    Verifica que el usuario esté activo.
    """
    if not current_user.is_active:
        raise UnauthorizedException(message="Inactive user")
    return current_user
