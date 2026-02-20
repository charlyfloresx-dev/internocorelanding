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
        # Rutas que NO requieren validación de X-Company-ID ni correspondencia de token
        path = request.url.path
        if path.startswith(
            ("/api/v1/auth/login", "/api/v1/auth/select-company", "/docs", "/openapi.json")
        ) or path == "/":
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
        if "company_id" in payload and payload["company_id"] != x_company_id:
             return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"status": "error", "message": "Tenant Mismatch: Header company does not match token."}
            )

        return await call_next(request)

class BlacklistMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Implementación placeholder para Blacklist
        return await call_next(request)