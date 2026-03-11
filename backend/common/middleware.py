import uuid
import logging
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
from common.domain.entities.user_context import UserContext

logger = logging.getLogger(__name__)

class InternoCoreGlobalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path.lower()
        
        # 1. IDENTIFICACIÓN DE RUTAS PÚBLICAS (Ultra-específica)
        is_public_route = any(x in path for x in [
            "/auth/login", 
            "/auth/select-company",
            "/public/register-company",
            "/internal/",
            "/admin/",
            "/docs", 
            "/openapi.json", 
            "/redoc", 
            "/static", 
            "/health",
            "/billing/webhook",
            "/favicon.ico"
        ]) or path == "/"

        # 2. CONFIGURACIÓN DE SEGUIMIENTO (Estandarización de trace_id)
        transaction_id = request.headers.get("X-Trace-Id") or \
                         request.headers.get("X-Correlation-ID") or \
                         request.headers.get("X-Transaction-ID") or \
                         str(uuid.uuid4())
        
        request.state.transaction_id = transaction_id 
        start_time = time.time()
        
        # 3. VALIDACIÓN DE TENANT (Solo para rutas PRIVADAS)
        company_id = request.headers.get("X-Company-ID")
        user_id = None
        group_id = None
        
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                import base64
                parts = token.split(".")
                if len(parts) == 3:
                    payload_b64 = parts[1]
                    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                    payload_json = base64.urlsafe_b64decode(payload_b64).decode("utf-8")
                    payload = json.loads(payload_json)
                    
                    if not company_id and payload.get("company_id"):
                        company_id = payload.get("company_id")
                    user_id = payload.get("sub")
                    group_id = payload.get("group_id")

                    if payload.get("type") == "selection":
                        request.state.user_token = None
                    else:
                        try:
                            from common.security.auth_payload import TokenPayload
                            token_payload = TokenPayload(**payload)
                            token_payload.token = token
                            request.state.user_token = token_payload
                        except Exception as e:
                            logger.error(f"❌ Middleware Token Validation Error: {e}")
                            pass
            except Exception:
                pass

        if not is_public_route and not company_id:
            is_selection = False
            if token:
                try:
                    import base64
                    payload_parts = token.split(".")
                    if len(payload_parts) == 3:
                        p_b64 = payload_parts[1]
                        p_b64 += "=" * ((4 - len(p_b64) % 4) % 4)
                        p_json = json.loads(base64.urlsafe_b64decode(p_b64).decode("utf-8"))
                        if p_json.get("type") == "selection":
                            is_selection = True
                except:
                    pass
            
            if not is_selection:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "Company ID could not be determined from headers or token",
                        "meta": {"trace_id": transaction_id}
                    }
                )

        # 4. SETEO DE CONTEXTO GLOBAL
        token_ctx = None
        if company_id or user_id:
            try:
                company_uuid = None
                if company_id and company_id != "None":
                    company_uuid = uuid.UUID(str(company_id))
                
                group_uuid = None
                if group_id and group_id != "None":
                    group_uuid = uuid.UUID(str(group_id))
                    
                user_ctx = UserContext(
                    company_id=company_uuid, 
                    user_id=str(user_id) if user_id else None,
                    group_id=group_uuid,
                    trace_id=transaction_id,
                    token=token
                )
                token_ctx = request_context.set(user_ctx)
            except (ValueError, TypeError):
                if company_id:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": "error",
                            "message": f"X-Company-ID header must be a valid UUID (Got: {company_id})",
                            "meta": {"trace_id": transaction_id}
                        }
                    )

        try:
            # 5. EJECUCIÓN DE LA PETICIÓN
            response = await call_next(request)
            
            # 6. FORMATEO DE RESPUESTA
            content_type = response.headers.get("content-type", "")
            
            # --- SALIDA RÁPIDA PARA RUTAS TÉCNICAS (Swagger, Redoc, OpenAPI) ---
            # Evita el "Unable to render this definition" al no envolver el JSON en ApiResponse
            if any(x in path for x in ["/openapi.json", "/docs", "/redoc"]):
                response.headers["X-Transaction-ID"] = transaction_id
                return response

            # --- SALIDA RÁPIDA PARA NO JSON ---
            if "application/json" not in content_type:
                response.headers["X-Transaction-ID"] = transaction_id
                return response

            # Procesamiento para todas las respuestas JSON restantes
            response_body = [section async for section in response.body_iterator]
            response_body_bytes = b"".join(response_body)
            
            try:
                original_data = json.loads(response_body_bytes.decode())
                latency_str = f"{time.time() - start_time:.4f}s"
                
                if isinstance(original_data, dict) and "status" in original_data and "meta" in original_data:
                    content = original_data
                    if not content["meta"].get("latency"):
                        content["meta"]["latency"] = latency_str
                    if not content["meta"].get("trace_id"):
                        content["meta"]["trace_id"] = transaction_id
                else:
                    is_success = 200 <= response.status_code < 300
                    content = ApiResponse(
                        status="success" if is_success else "error",
                        data=original_data if is_success else None,
                        message="Operación completada" if is_success else str(original_data.get("detail", "Error")),
                        meta=ApiMeta(
                            trace_id=transaction_id,
                            latency=latency_str
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
                response.headers["X-Transaction-ID"] = transaction_id
                response.body_iterator = iterate_in_threadpool(iter([response_body_bytes]))
                return response

        except Exception as e:
            from fastapi import HTTPException
            if isinstance(e, HTTPException):
                raise e
            
            import traceback
            traceback.print_exc()
            
            return JSONResponse(
                status_code=500, 
                content={
                    "status": "error", 
                    "message": f"Critical Middleware Error: {str(e)}",
                    "meta": {"trace_id": transaction_id}
                }
            )
        finally:
            if token_ctx:
                request_context.reset(token_ctx)