import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.database import get_db
from common.domain.entities.user_context import UserContext
from common.context import request_context

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8001/api/v1/auth/login"
)

async def get_current_user_payload(request: Request, token: Annotated[str, Depends(oauth2_scheme)] = None) -> UserContext:
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"]
        )
        user_id = payload.get("sub", "00000000-0000-0000-0000-000000000000")
        company_id = payload.get("company_id")
        
        user_context = UserContext(user_id=user_id, company_id=uuid.UUID(str(company_id)))
        request_context.set(user_context)
        return user_context

    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas o token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

get_current_user = get_current_user_payload
