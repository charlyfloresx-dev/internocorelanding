from fastapi import Request, HTTPException, status, Depends
from typing import Optional
from common.security.auth_payload import TokenPayload

# Nota: Esta clase asume que 'get_current_user' (o similar) ya validó el JWT 
# y lo inyectó como TokenPayload. Dependiendo de la arquitectura, 
# puede que el guardia necesite disparar la validación si no está en el pipeline.

class SubscriptionGuard:
    """
    Guardia de seguridad transversal para InternoCore.
    Valida derechos de acceso por módulo y restricciones de solo lectura.
    """
    def __init__(self, module_code: str):
        self.module_code = module_code

    async def __call__(self, request: Request, payload: any = None):
        """
        Lógica de validación. 
        payload debe ser de tipo TokenPayload.
        """
        # 1. Obtener payload (Si no se pasa por Depends, intentamos desde request.state)
        # Algunos servicios guardan el payload en request.state tras el middleware
        token_data: Optional[TokenPayload] = payload or getattr(request.state, "user_token", None)
        
        if not token_data:
            trace_id = getattr(request.state, "transaction_id", "N/A")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Sesión no válida. Ref: [{trace_id}]"
            )

        # 2. Validación de Módulo (Entitlement)
        if self.module_code != "auth_core":
            user_modules = [m.lower() for m in token_data.modules]
            if self.module_code.lower() not in user_modules:
                trace_id = getattr(request.state, "transaction_id", "N/A")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Módulo [{self.module_code}] no activo. Ref: [{trace_id}]"
                )

        # 3. Validación de Solo Lectura (Read-Only Mode)
        if token_data.readonly:
            if request.method not in ["GET", "HEAD", "OPTIONS"]:
                trace_id = getattr(request.state, "transaction_id", "N/A")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Modo lectura activo. Complete su pago. Ref: [{trace_id}]"
                )
        
        return token_data
