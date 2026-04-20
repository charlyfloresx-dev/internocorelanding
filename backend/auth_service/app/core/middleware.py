from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_token
import uuid

class TenantSecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware para validar la coherencia entre el header X-Company-ID y el token JWT.
    Se salta la validación para rutas públicas (Login, Health, Docs).
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Rutas Blancas (Exclusiones)
        path = request.url.path.rstrip("/")
        normalized_path = path.lower()
        
        WHITELIST = [
            "/api/v1/auth/login",
            "/api/v1/auth/social-login",
            "/api/v1/auth/select-company",
            "/api/v1/auth/collaborator/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/request-password-reset",
            "/api/v1/auth/confirm-password-reset",
            "/api/v1/health/demo",
            "/docs",
            "/openapi.json"
        ]
        
        # DEBUG AGRESIVO
        # print(f"DEBUG: Middleware Checking Path='{normalized_path}'")
        
        is_exempt = any(normalized_path.endswith(w.lower()) for w in WHITELIST) or normalized_path in ["", "/", "/api/v1", "/api/v2"]

        if is_exempt:
            return await call_next(request)

        # 2. Obtener Header y Token
        x_company_id = request.headers.get("x-company-id")
        auth_header = request.headers.get("authorization")

        if not x_company_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "x-company-id header is missing"}
            )

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "error", "message": "Missing or invalid Authorization header"}
            )

        token = auth_header.split(" ")[1]
        payload = decode_token(token)

        if not payload:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"status": "error", "message": "Invalid token"}
            )

        # 3. Validación Cruzada (Solo si el token tiene company_id)
        # Nota: Los tokens de selección no tienen company_id, pero esas rutas están en la lista blanca.
        
        # [GOD MODE] Si el token tiene el claim de bypass, permitimos cualquier tenant
        if payload.get("bypass_tenant") is True:
            return await call_next(request)

        if "company_id" in payload and payload.get("company_id") and x_company_id:
            if str(payload["company_id"]).lower() != str(x_company_id).lower():
                 return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"status": "error", "message": f"Tenant Mismatch: Header company {x_company_id} does not match token {payload['company_id']}."}
                )

        return await call_next(request)

class BlacklistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Implementación placeholder para Blacklist
        return await call_next(request)