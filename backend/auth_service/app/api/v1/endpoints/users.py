from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import List, Optional

# 1. Imports de Core
from app.core.security import get_password_hash  # <--- OJO: Verifica si se llama hash_password o get_password_hash en tu security.py
from app.core.database import get_db 
from app.deps import get_current_tenant_context, SecurityContext

# 2. Modelos Reales (Separados por archivo como definimos en el ADN)
from app.models.user import User 
from app.models.user_company_role import UserCompanyRole
from app.models.role import Role

# 3. Schemas
from app.schemas.user import UserCreate, UserResponse 

# 4. Common (Clean Architecture)
from common.responses import ApiResponse
from common.repository import BaseRepository
from common.exceptions import DomainException

router = APIRouter()

@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(get_current_tenant_context)
):
    # Obtener Company ID del contexto
    company_id = context.company_id
    
    # Repositorio con Scope de Tenant
    user_repo = BaseRepository(User, db, company_id=company_id) 

    # Verificar existencia
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise DomainException(message="User already exists in this company", code="USER_EXISTS")

    # Crear Usuario
    user_data = user_in.model_dump()
    raw_password = user_data.pop("password")
    user_data["hashed_password"] = get_password_hash(raw_password)

    new_user = await user_repo.create(user_data)

    # Buscar el rol 'operator' en la tabla de roles
    role_stmt = select(Role).where(Role.name == "operator")
    role_result = await db.execute(role_stmt)
    default_role = role_result.scalar_one_or_none()
    
    # Crear vínculo de membresía
    membership = UserCompanyRole(
        user_id=new_user.id,
        company_id=company_id,
        role_id=default_role.id if default_role else None,
        is_new=True,
        scopes=["catalog:read", "inventory:read"] 
    )
    db.add(membership)
    
    await db.commit()
    await db.refresh(new_user)

    return ApiResponse(
        status="success",
        data=UserResponse.model_validate(new_user),
        message="User created successfully in this company"
    )