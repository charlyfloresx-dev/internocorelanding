from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
import uuid
from typing import List, Optional

from auth_app.dependencies import get_db
from auth_app.models.user import User
from auth_app.models.user_company_role import UserCompanyRole
from auth_app.models.role import Role
from common.config import settings
from common.repository import BaseRepository
from common.responses import ApiResponse
from auth_app.core.security import create_admin_god_token, create_god_mode_token
from common.services.audit_service import AuditService
from common.security.subscription_guard import SubscriptionGuard
from common.security.auth_payload import TokenPayload
from common.security.limiter import limiter
from common.security.dependencies import get_redis
import logging

audit_logger = logging.getLogger("security.god_mode")

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
    [GOD MODE] Intercambia el Master Key por un JWT de Rescate Técnico (30 min).
    Legacy — usar /elevate para nuevas integraciones con el panel frontend.
    """
    transaction_id = getattr(request.state, "transaction_id", str(uuid.uuid4()))
    audit_logger.critical(
        "[GOD_MODE_HANDSHAKE] user=%s ip=%s tx=%s",
        user_id,
        request.client.host if request.client else "unknown",
        transaction_id,
    )
    token = create_admin_god_token(subject=user_id, correlation_id=transaction_id)
    return ApiResponse(
        status="success",
        message="God Mode Handshake successful. Token generated.",
        data={"access_token": token, "token_type": "bearer", "expires_in": 1800},
    )


@router.post("/elevate", response_model=ApiResponse)
@limiter.limit("3/hour")
async def god_mode_elevate(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_admin_master_key: str = Header(..., alias="X-Admin-Master-Key"),
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
):
    """
    [GOD MODE] Panel de emergencia frontend — valida la master key y emite un token
    de 300 segundos (5 min) con scopes wildcard y JTI rastreable en Redis.
    Rate limit: 3 intentos / hora / IP.
    """
    if not x_admin_master_key or x_admin_master_key != settings.int_admin_master_key:
        audit_logger.warning(
            "[GOD_MODE_ELEVATE_FAIL] ip=%s ua=%s",
            request.client.host if request.client else "unknown",
            request.headers.get("user-agent", "")[:80],
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "ERR_INVALID_MASTER_KEY", "message": "Llave maestra inválida."},
        )

    correlation_id = str(uuid.uuid4())
    company_id = uuid.UUID(x_company_id) if x_company_id else None
    # Sujeto sintético para sesiones god-mode sin usuario DB
    god_subject = uuid.UUID("00000000-0000-0000-0000-000000000000")

    token, jti = create_god_mode_token(
        subject=god_subject,
        company_id=company_id,
        correlation_id=correlation_id,
    )

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:255]

    # Registro crítico — ambos canales (logger + DB) para máxima trazabilidad
    audit_logger.critical(
        "[SECURITY_ALERT] GOD_MODE_ACTIVATED via /elevate | ip=%s | ua=%s | company=%s | jti=%s | trace=%s",
        client_ip, user_agent[:80], x_company_id, jti, correlation_id,
    )
    await AuditService.log_action(
        db=db,
        user_id="GOD_MODE_ELEVATE",
        action="GOD_MODE_ACTIVATED",
        entity_name="system_access",
        entity_id=x_company_id or "GLOBAL",
        ip_address=client_ip,
        user_agent=user_agent,
        new_value={
            "jti": jti,
            "company_id": x_company_id,
            "correlation_id": correlation_id,
            "expires_in": 300,
        },
    )
    await db.commit()

    # Registrar JTI en Redis — clave de vida para revocación server-side
    # Si Redis no está disponible, el token igual expira por TTL del JWT (fail-safe)
    try:
        r = get_redis()
        await r.set(f"godmode:{jti}", "1", ex=300)
    except Exception as redis_err:
        audit_logger.warning("[GOD_MODE] Redis write failed — JTI not registered, revocation unavailable: %s", redis_err)

    return ApiResponse(
        status="success",
        message="Sesión de emergencia activada. Esta sesión está siendo estrictamente auditada.",
        data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 300,
            "metadata": {
                "scope": ["*"],
                "role": "admin",
                "jti": jti,
                "warning": "Esta sesión está siendo estrictamente auditada en el log del servidor.",
            },
        },
    )


@router.delete("/elevate/{jti}", response_model=ApiResponse)
async def revoke_god_mode(
    jti: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="auth_core")),
):
    """
    Revocación anticipada de una sesión GOD MODE por JTI.
    Requiere token activo con rol admin/owner o scopes wildcard.
    """
    is_authorized = (token.scopes and "*" in token.scopes) or token.role.lower() in ("admin", "owner")
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR_INSUFFICIENT_SCOPE", "message": "Se requiere rol admin para revocar sesiones."},
        )

    try:
        r = get_redis()
        deleted = await r.delete(f"godmode:{jti}")
    except Exception as redis_err:
        audit_logger.error("[GOD_MODE_REVOKE] Redis error: %s", redis_err)
        raise HTTPException(status_code=503, detail={"code": "ERR_REDIS_UNAVAILABLE", "message": "No se pudo contactar Redis."})

    client_ip = request.client.host if request.client else "unknown"
    audit_logger.critical(
        "[SECURITY_ALERT] GOD_MODE_REVOKED | jti=%s | revoked_by=%s | ip=%s | found=%s",
        jti, str(token.sub), client_ip, bool(deleted),
    )
    await AuditService.log_action(
        db=db, user_id=str(token.sub), action="GOD_MODE_REVOKED",
        entity_name="system_access", entity_id=jti,
        ip_address=client_ip, new_value={"jti": jti, "was_active": bool(deleted)},
    )
    await db.commit()

    return ApiResponse(
        status="success",
        data={"jti": jti, "revoked": bool(deleted)},
        message="Sesión de emergencia revocada." if deleted else "JTI no encontrado (ya expiró o fue revocado).",
    )


@router.get("/security-logs", response_model=ApiResponse)
async def get_security_logs(
    request: Request,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="auth_core")),
):
    """
    Panel de alertas de seguridad — eventos GOD_MODE y SECURITY_ALERT del audit trail.
    Requiere JWT con scopes wildcard o rol admin.
    """
    is_god_mode  = bool(token.scopes and "*" in token.scopes)
    is_admin_role = token.role.lower() in ("admin", "owner") or any(
        r.lower() in ("admin", "owner") for r in (token.role_names or [])
    )
    if not (is_god_mode or is_admin_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ERR_INSUFFICIENT_SCOPE", "message": "Se requiere rol admin o sesión GOD MODE."},
        )

    rows = await db.execute(
        text("""
            SELECT
                id,
                action        AS event_type,
                action        AS message,
                client_ip     AS ip_address,
                user_agent,
                timestamp,
                new_value
            FROM audit_logs
            WHERE action LIKE 'GOD_MODE%' OR action LIKE 'SECURITY_ALERT%'
            ORDER BY timestamp DESC
            LIMIT :limit
        """).execution_options(ignore_tenant_filter=True),
        {"limit": min(limit, 200)},
    )
    events = [
        {
            "id": str(row.id),
            "event_type": "SECURITY_ALERT",
            "message": row.event_type,
            "ip_address": row.ip_address or "unknown",
            "user_agent": row.user_agent or "unknown",
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "metadata": row.new_value or {},
        }
        for row in rows
    ]
    return ApiResponse(status="success", data=events, message=f"{len(events)} security events found.")
