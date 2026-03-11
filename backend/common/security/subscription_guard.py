from fastapi import Request, HTTPException, status, Depends
from typing import Optional, Any
import uuid
from common.security.auth_payload import TokenPayload

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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Sesión no válida o token ausente.",
                    "code": "ERR_UNAUTHORIZED",
                    "transaction_id": trace_id
                }
            )

        # 2. Validación de Módulo (Entitlements)
        # Si no es un módulo núcleo (auth), validamos que esté en el claim 'modules'
        if self.module_code != "auth_core":
            user_modules = [m.lower() for m in token_data.modules]
            if self.module_code.lower() not in user_modules:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": f"Módulo [{self.module_code}] no está incluido en su plan actual.",
                        "code": "ERR_SUBSCRIPTION_REQUIRED",
                        "transaction_id": trace_id
                    }
                )

        # 3. Validación de Modo Lectura (Gobernanza - Kill Switch Fase 1)
        # Si readonly es true, bloqueamos métodos de escritura (POST, PUT, PATCH, DELETE)
        if token_data.readonly:
            if request.method not in ["GET", "HEAD", "OPTIONS"]:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "error": "Suscripción vencida. Modo lectura activo para protección de datos.",
                        "code": "ERR_SUBSCRIPTION_REQUIRED",
                        "transaction_id": trace_id
                    }
                )
        
        return token_data
