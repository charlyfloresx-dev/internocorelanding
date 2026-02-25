import uuid
import time
import json
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.concurrency import iterate_in_threadpool
from common.responses import ApiResponse, ApiMeta
from common.context import request_context
from common.models.user_context import UserContext

class InternoCoreGlobalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.lower()
        
        # 1. IDENTIFICACIÓN DE RUTAS PÚBLICAS (Ultra-específica)
        # Agregamos todas las variantes de Swagger y archivos estáticos
        is_public_route = any(x in path for x in [
            "/auth/login", 
            "/auth/select-company",  # <--- AGREGA ESTO
            "/docs", 
            "/openapi.json", 
            "/redoc", 
            "/static", 
            "/health",
            "/favicon.ico"
        ]) or path == "/"

        # 2. CONFIGURACIÓN DE SEGUIMIENTO
        transaction_id = request.headers.get("X-Transaction-ID", str(uuid.uuid4()))
        request.state.transaction_id = transaction_id 
        start_time = time.time()
        
        # 3. VALIDACIÓN DE TENANT (Solo para rutas PRIVADAS)
        company_id = request.headers.get("X-Company-Id")
        
        if not is_public_route and not company_id:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "X-Company-Id header is required for private routes",
                    "meta": {"trace_id": transaction_id}
                }
            )

        # 4. SETEO DE CONTEXTO GLOBAL
        token = None
        if company_id:
            try:
                company_uuid = uuid.UUID(company_id)
                user_ctx = UserContext(company_id=company_uuid)
                token = request_context.set(user_ctx)
            except (ValueError, TypeError):
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "X-Company-Id header must be a valid UUID",
                        "meta": {"trace_id": transaction_id}
                    }
                )

        try:
            # 5. EJECUCIÓN DE LA PETICIÓN
            response = await call_next(request)
            
            # 6. FORMATEO DE RESPUESTA
            content_type = response.headers.get("content-type", "")
            
            # --- SALIDA RÁPIDA PARA RUTAS PÚBLICAS O NO JSON ---
            # Esto evita que el middleware intente procesar el openapi.json
            if is_public_route or "application/json" not in content_type:
                response.headers["X-Transaction-ID"] = transaction_id
                return response

            # Procesamiento para rutas de negocio (Privadas)
            response_body = [section async for section in response.body_iterator]
            response_body_bytes = b"".join(response_body)
            
            try:
                original_data = json.loads(response_body_bytes.decode())
                
                # Evitar doble formateo si ya viene ApiResponse
                if isinstance(original_data, dict) and "status" in original_data and "meta" in original_data:
                    content = original_data
                else:
                    is_success = 200 <= response.status_code < 300
                    content = ApiResponse(
                        status="success" if is_success else "error",
                        data=original_data if is_success else None,
                        message="Operación completada" if is_success else str(original_data.get("detail", "Error")),
                        meta=ApiMeta(
                            trace_id=transaction_id,
                            latency=f"{time.time() - start_time:.4f}s"
                        )
                    ).model_dump(exclude_none=False)

                new_headers = dict(response.headers)
                new_headers.pop("content-length", None) 
                new_headers["X-Transaction-ID"] = transaction_id

                return JSONResponse(
                    status_code=response.status_code, 
                    content=content, 
                    headers=new_headers
                )

            except Exception:
                # Fallback si falla el parseo de JSON
                response.headers["X-Transaction-ID"] = transaction_id
                response.body_iterator = iterate_in_threadpool(iter([response_body_bytes]))
                return response

        except Exception as e:
            return JSONResponse(
                status_code=500, 
                content={
                    "status": "error", 
                    "message": f"Critical Middleware Error: {str(e)}",
                    "meta": {"trace_id": transaction_id}
                }
            )
        finally:
            if token:
                request_context.reset(token)