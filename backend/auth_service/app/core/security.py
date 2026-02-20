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
    subject: uuid.UUID, company_id: uuid.UUID, roles: List[str], scopes: List[str]
) -> str:
    """Crea el JWT final que incluye roles y scopes."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "company_id": str(company_id),
        "role_names": roles,
        "scopes": scopes,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

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