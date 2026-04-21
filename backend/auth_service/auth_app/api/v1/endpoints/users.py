from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import random
import string
from typing import List, Optional

from auth_app.dependencies import get_db, get_current_tenant_context, SecurityContext
from auth_app.core.security import get_password_hash

# 2. Modelos Reales
from auth_app.models.user import User 
from auth_app.models.user_company_role import UserCompanyRole
from auth_app.models.role import Role
from auth_app.models.invitation import Invitation
from auth_app.models.company import Company

# 3. Schemas
from auth_app.schemas.user import UserCreate, UserResponse 
from auth_app.schemas.invitation import InvitationCreate, InvitationResponse

# 4. Common (Clean Architecture)
from common.responses import ApiResponse
from common.repository import BaseRepository
from common.exceptions import DomainException
from common.services.notification_client import notification_client # Ahora delegamos al Notification Service

router = APIRouter()

@router.get("/", response_model=ApiResponse[List[UserResponse]])
async def list_company_users(
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(get_current_tenant_context)
):
    """
    Lista todos los usuarios que pertenecen a la empresa del contexto actual.
    Filtra a través de la tabla user_company_roles.
    """
    company_id = context.company_id
    
    # Query para traer usuarios unidos por su relación con la empresa
    stmt = (
        select(User)
        .join(UserCompanyRole, User.id == UserCompanyRole.user_id)
        .where(UserCompanyRole.company_id == company_id)
    )
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return ApiResponse(
        status="success",
        data=[UserResponse.model_validate(u) for u in users],
        message=f"Found {len(users)} users for company {company_id}"
    )

@router.post("/invite", response_model=ApiResponse[InvitationResponse])
async def create_invitation(
    invite_in: InvitationCreate,
    db: AsyncSession = Depends(get_db),
    context: SecurityContext = Depends(get_current_tenant_context)
):
    """
    Genera un código de invitación para un nuevo usuario y envía el correo.
    """
    company_id = context.company_id
    
    # Validar que el rol existe
    role = await db.get(Role, invite_in.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Obtener nombre de la empresa para el correo
    company = await db.get(Company, company_id)
    company_name = company.name if company else "Interno Core Platform"

    # Generar código único de 8 caracteres (Alfanumérico)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    new_invitation = Invitation(
        email=invite_in.email,
        code=code,
        role_id=invite_in.role_id,
        company_id=company_id,
        is_used=False
    )
    
    db.add(new_invitation)
    try:
        await db.commit()
        await db.refresh(new_invitation)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error creating invitation. Maybe email already invited?")

    # DELEGAR A NOTIFICATION SERVICE (Vía common/notification_client)
    await notification_client.send_user_invitation(
        email=invite_in.email,
        code=code,
        company_name=company_name,
        company_id=str(company_id)
    )

    return ApiResponse(
        status="success",
        data=InvitationResponse.model_validate(new_invitation),
        message=f"Invitation code generated and sent to {invite_in.email}"
    )

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
