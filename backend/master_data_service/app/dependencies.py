from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.product_service import ProductService
from common.models.user_context import UserContext
from common.middleware import request_context
# Nota: Se asume que 'common.security' provee la decodificación del token.
# Si no está disponible, se debe implementar la decodificación JWT aquí.
# from common.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8001/api/v1/auth/login"
)

async def get_current_user_payload(token: Annotated[str, Depends(oauth2_scheme)]) -> UserContext:
    """
    Valida el token JWT y asegura que exista un contexto de compañía.
    """
    # Simulación de decodificación (Reemplazar con lógica real de common)
    # payload = decode_access_token(token)
    # Mock para estructura con un UUID válido
    payload = {"sub": "user_id", "company_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"}

    # Validación de Aislamiento Multitenant
    company_id = payload.get("company_id")
    
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No company context found in token. Multitenancy violation."
        )
    
    user_context = UserContext(user_id=payload.get("sub"), company_id=company_id)
    
    # Inyectar en el ContextVar para acceso global (Repositorios, Auditoría)
    request_context.set(user_context)
    
    return user_context

async def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(db)

# Alias para compatibilidad con endpoints que aún importan el nombre antiguo
get_current_user = get_current_user_payload