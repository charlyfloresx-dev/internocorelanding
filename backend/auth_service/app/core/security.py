import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- ALIAS DE COMPATIBILIDAD ---
# Esto evita el ImportError en users.py y otros módulos
hash_password = get_password_hash 

def create_final_access_token(
    subject: uuid.UUID, 
    company_id: uuid.UUID, 
    roles: List[str], 
    scopes: List[str],
    group_id: Optional[uuid.UUID] = None,
    modules: List[str] = ["auth_core", "inventory_core"],
    status: str = "TRIAL",
    readonly: bool = False,
    correlation_id: Optional[str] = None
) -> str:
    """
    Crea el JWT final que incluye roles, scopes, módulos habilitados, estado de suscripción y correlation_id.
    
    # TODO: Validar status EXPIRED en DB de suscripciones antes de emitir T2 (Kill Switch)
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "company_id": str(company_id),
        "group_id": str(group_id) if group_id else None,
        "role_names": roles,
        "scopes": scopes,
        "modules": modules,
        "status": status,
        "readonly": readonly,
        "correlation_id": correlation_id
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_access_token(
    subject: str,
    company_id: str,
    data: dict
) -> str:
    """
    Función de compatibilidad para generar el token final enriquecido.
    """
    return create_final_access_token(
        subject=uuid.UUID(subject),
        company_id=uuid.UUID(company_id),
        roles=data.get("role_names", []),
        scopes=data.get("scopes", []),
        modules=data.get("modules", ["auth_core", "inventory_core"]),
        status=data.get("status", "TRIAL"),
        readonly=data.get("readonly", False),
        correlation_id=data.get("correlation_id")
    )

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.JWTError:
        return None

def create_selection_token(subject: uuid.UUID) -> str:
    """Crea un token temporal para la fase de selección de empresa."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.SELECTION_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "selection"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt