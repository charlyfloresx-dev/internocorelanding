from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.product_service import ProductService
from common.domain.entities.user_context import UserContext
from common.context import request_context

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8001/api/v1/auth/login"
)

async def get_current_user_payload(request: Request, token: Annotated[str, Depends(oauth2_scheme)] = None) -> UserContext:
    """
    Valida el token JWT y asegura que exista un contexto de compañía.
    En este microservicio Master Data, priorizamos el header X-Company-ID para integraciones internas.
    """
    company_id = request.headers.get("X-Company-ID")
    user_id = "00000000-0000-0000-0000-000000000000" # System User fallback

    if not company_id:
        # Si no hay header, intentamos mock (solo para desarrollo/test local si el token es bearer)
        company_id = "00000000-0000-0000-0000-000000000001"
    
    user_context = UserContext(user_id=user_id, company_id=uuid.UUID(str(company_id)))
    
    # Inyectar en el ContextVar para acceso global
    request_context.set(user_context)
    
    return user_context

async def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(db)

# Alias para compatibilidad con endpoints que aún importan el nombre antiguo
get_current_user = get_current_user_payload