import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.config import settings
from app.database import get_db
from app import models, schemas
# CORRECCIÓN: Importar el servicio desde la nueva ruta correcta
from app.services.auth_service import AuthService

# CORRECCIÓN: Asegurar bcrypt__ident="2b" para compatibilidad total
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

class AuthHandler:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
        
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
        
    def create_access_token(self, user: models.User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # CORRECCIÓN: La estructura del payload debe reflejar la nueva arquitectura
        # donde el usuario tiene acceso a múltiples compañías.
        payload = {
            "exp": expire, 
            "iat": datetime.now(timezone.utc),
            "sub": str(user.id),
            # company_id y roles se gestionarán en un token separado (T2)
            # o se extraerán del contexto al loguearse.
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

auth_handler = AuthHandler()

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload_dict = auth_handler.decode_token(token)
    payload = schemas.TokenPayload(**payload_dict)
    
    # CORRECCIÓN: Uso explícito de AuthService desde la nueva ubicación
    user = await AuthService.get_user_by_id(db, user_id=uuid.UUID(payload.sub))
    
    if user is None or not user.is_active:
        raise credentials_exception
    return user