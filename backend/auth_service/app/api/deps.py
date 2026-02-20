from typing import Generator, Optional
from fastapi import Depends, Header
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import ALGORITHM
from app.models import User
from common.exceptions import UnauthorizedException, NotFoundException

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Header(..., alias="Authorization")
) -> User:
    """
    Valida el token JWT y recupera el usuario.
    Lanza UnauthorizedException con código estructurado si falla.
    """
    try:
        # Remover prefijo 'Bearer ' si existe
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
            
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedException(
                message="Could not validate credentials",
                details={"reason": "Missing subject in token"}
            )
    except JWTError:
        raise UnauthorizedException(
            message="Could not validate credentials",
            details={"reason": "Invalid token signature or expired"}
        )
    
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundException(entity="User", entity_id=user_id)
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise UnauthorizedException(
            message="Inactive user",
            details={"reason": "User account is disabled"}
        )
    return current_user

def get_company_id_header(x_company_id: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extrae el ID de la compañía del header para operaciones multi-tenant.
    """
    return x_company_id