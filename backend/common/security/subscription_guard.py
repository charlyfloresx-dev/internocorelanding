from fastapi import Request, HTTPException, status, Depends
from typing import Optional, Any
import uuid
from common.security.auth_payload import TokenPayload
from common.config import settings

class SubscriptionGuard:
    """
    Guardia de seguridad transversal para InternoCore.
    Implementa el flujo de denegación por suscripción y modo solo lectura.
    """
    def __init__(self, module_code: str):
        self.module_code = module_code

    async def __call__(self, request: Request, payload: Any = None):
        """
        Lógica de validación de suscripción y gobernanza.
        """
        # 1. Obtener payload y traza
        token_data: Optional[TokenPayload] = payload or getattr(request.state, "user_token", None)
        trace_id = getattr(request.state, "transaction_id", None) or str(uuid.uuid4())
        
        if not token_data:
            # GOD MODE (break-glass): valida sin fallback — falla cerrado si la clave no está configurada
            master_key = settings.int_admin_master_key
            provided_key = request.headers.get("X-Admin-Master-Key", "")
            if provided_key and provided_key == master_key:
                company_id = request.headers.get("X-Company-ID")
                token_data = TokenPayload(
                    sub=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                    company_id=uuid.UUID(company_id) if company_id else None,
                    role="GOD_MODE_ADMIN",
                    role_names=["admin"],
                    scopes=["*"],
                    modules=["auth_core", "inventory_core", "master_data_core", "hr_core"],
                    status="ACTIVE",
                    readonly=False,
                    accessible_warehouses=[]
                )
                request.state.user_token = token_data

                # Registro inmutable de cada activación — siempre, sin excepciones
                import logging as _logging
                _sec_log = _logging.getLogger("security.god_mode")
                _sec_log.critical(
                    "[SECURITY_ALERT] GOD_MODE_ACTIVATED | ip=%s | ua=%s | company=%s | path=%s | trace=%s",
                    request.client.host if request.client else "unknown",
                    request.headers.get("user-agent", "unknown")[:120],
                    company_id,
                    request.url.path,
                    trace_id,
                )
                # Audit DB (fire-and-forget aceptable aquí porque es un evento de seguridad,
                # no de negocio — el logger crítico ya garantiza la trazabilidad)
                try:
                    from common.infrastructure.database import AsyncSessionLocal
                    from common.services.audit_service import AuditService
                    import asyncio

                    async def _log_god_mode():
                        async with AsyncSessionLocal() as _db:
                            await AuditService.log_action(
                                db=_db,
                                user_id="GOD_MODE",
                                action="GOD_MODE_ACTIVATED",
                                entity_name="system_access",
                                entity_id=company_id,
                                ip_address=request.client.host if request.client else "unknown",
                                user_agent=request.headers.get("user-agent", "unknown")[:255],
                                new_value={
                                    "path": request.url.path,
                                    "method": request.method,
                                    "trace_id": trace_id,
                                },
                            )
                            await _db.commit()

                    asyncio.create_task(_log_god_mode())
                except Exception:
                    pass  # El logger crítico ya tiene el evento — no propagar error aquí
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "status": "error",
                        "message": "Sesión no válida o token ausente.",
                        "code": "ERR_UNAUTHORIZED",
                        "meta": {"trace_id": trace_id}
                    }
                )

        # 2. Validación de Módulo (Entitlements)
        if self.module_code != "auth_core":
            # [Industrial Bypass] Admin roles (*) bypass module entitlement checks
            if "*" in token_data.scopes:
                return token_data

            user_modules = [m.lower() for m in token_data.modules]
            if self.module_code.lower() not in user_modules:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "status": "error",
                        "message": f"Módulo [{self.module_code}] no está incluido en su plan actual.",
                        "code": "ERR_SUBSCRIPTION_REQUIRED",
                        "meta": {"trace_id": trace_id}
                    }
                )

        # 3. Validación de Modo Lectura (Gobernanza - Kill Switch Fase 1)
        if token_data.readonly:
            if request.method not in ["GET", "HEAD", "OPTIONS"]:
                # Log the forensic event before raising the exception
                try:
                    from common.infrastructure.database import AsyncSessionLocal
                    from common.services.audit_service import AuditService
                    import asyncio
                    
                    async def log_block():
                        async with AsyncSessionLocal() as session:
                            audit_service = AuditService(session)
                            await audit_service.log_action(
                                user_id=str(token_data.sub),
                                company_id=str(token_data.company_id),
                                tenant_id=str(token_data.company_id),
                                table_name="system_access",
                                action="ACCESS_DENIED_402",
                                old_values={"status": token_data.status},
                                new_values={"reason": "Subscription PAST_DUE", "method": request.method, "path": request.url.path},
                                ip_address=request.client.host if request.client else "unknown",
                                user_agent=request.headers.get("user-agent", "unknown")
                            )
                            await session.commit()
                            
                    # Fire and forget
                    asyncio.create_task(log_block())
                except Exception as e:
                    import logging
                    logging.error(f"Failed to log ACCESS_DENIED_402 event: {e}")

                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "status": "error",
                        "message": "Suscripción en mora. El sistema ha activado el Modo Lectura. Por favor regularice su pago para habilitar ediciones.",
                        "code": "ERR_READONLY_MODE",
                        "meta": {"trace_id": trace_id}
                    }
                )
        
        return token_data
