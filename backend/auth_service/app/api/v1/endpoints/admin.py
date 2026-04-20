from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from typing import List

from app.dependencies import get_db
from app.models.user import User
from app.models.user_company_role import UserCompanyRole
from app.models.role import Role
from common.config import settings
from common.repository import BaseRepository
from common.responses import ApiResponse
from app.core.security import create_admin_god_token
import logging

audit_logger = logging.getLogger("auth_service.admin_audit")

router = APIRouter()

async def verify_admin_master_key(x_admin_key: str = Header(..., alias="X-Admin-Master-Key")):
    """
    Validador de llave maestra para acceso administrativo directo (God Mode).
    """
    if not settings or not settings.int_admin_master_key or x_admin_key != settings.int_admin_master_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso Denegado: Admin Master Key inválida o no configurada."
        )

@router.post("/users/force-assign", dependencies=[Depends(verify_admin_master_key)], response_model=ApiResponse)
async def force_assign_user(
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    role_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    [GOD MODE] Asignación forzada de un usuario a una empresa ignorando flujo de invitación.
    """
    transaction_id = getattr(request.state, "transaction_id", str(uuid.uuid4()))
    
    # EMITIR LOG ANTES DE LA TRANSACCIÓN
    print(f"[GOD_MODE] | Action: FORCE_ASSIGN_USER | Target: {user_id} | Company: {company_id} | TX: {transaction_id}")

    # Verificar existencia de usuario y empresa (Sin filtro de tenant)
    user_repo = BaseRepository(User, db)
    user = await user_repo.get(user_id, bypass_tenant=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verificar si el vínculo ya existe
    ucr_repo = BaseRepository(UserCompanyRole, db)
    # Buscamos manualmente ya que UserCompanyRole tiene PK compuesta
    stmt = select(UserCompanyRole).where(
        (UserCompanyRole.user_id == user_id) & (UserCompanyRole.company_id == company_id)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # Si ya existe, actualizamos el rol
        existing.role_id = role_id
        existing.is_new = False
        message = "User company association updated successfully via God Mode"
    else:
        # Crear nueva asociación
        new_ucr = UserCompanyRole(
            user_id=user_id,
            company_id=company_id,
            role_id=role_id,
            is_new=False,
            scopes=["*"]
        )
        db.add(new_ucr)
        message = "User assigned to company successfully via God Mode"

    await db.commit()
    
    return ApiResponse(
        status="success",
        message=message,
        data={"transaction_id": transaction_id}
    )

@router.patch("/roles/force-update", dependencies=[Depends(verify_admin_master_key)], response_model=ApiResponse)
async def force_role_update(
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    new_role_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    [GOD MODE] Elevación de privilegios administrativa.
    """
    transaction_id = getattr(request.state, "transaction_id", str(uuid.uuid4()))
    
    # EMITIR LOG ANTES DE LA TRANSACCIÓN
    print(f"[GOD_MODE] | Action: FORCE_ROLE_UPDATE | Target: {user_id} | Company: {company_id} | TX: {transaction_id}")

    stmt = select(UserCompanyRole).where(
        (UserCompanyRole.user_id == user_id) & (UserCompanyRole.company_id == company_id)
    )
    result = await db.execute(stmt)
    ucr = result.scalar_one_or_none()

    if not ucr:
        raise HTTPException(status_code=404, detail="User not associated with this company")

    ucr.role_id = new_role_id
    await db.commit()

    return ApiResponse(
        status="success",
        message="User role updated successfully via God Mode",
        data={"transaction_id": transaction_id}
    )

@router.post("/handshake", dependencies=[Depends(verify_admin_master_key)], response_model=ApiResponse)
async def god_mode_handshake(
    user_id: uuid.UUID,
    request: Request
):
    """
    [GOD MODE] Intercambia el Master Key por un JWT de Rescate Técnico.
    El token emitido permite el bypass de tenant por 30 minutos.
    """
    transaction_id = getattr(request.state, "transaction_id", str(uuid.uuid4()))
    
    # REGISTRO INMUTABLE (Simulado con Logger específico de Auditoría)
    audit_logger.warning(
        f"[AUDIT][GOD_MODE_HANDSHAKE] | User: {user_id} | TX: {transaction_id} | IP: {request.client.host}"
    )

    token = create_admin_god_token(subject=user_id, correlation_id=transaction_id)
    
    return ApiResponse(
        status="success",
        message="God Mode Handshake successful. Token generated.",
        data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 1800
        }
    )
