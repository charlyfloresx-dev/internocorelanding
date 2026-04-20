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
from common.security.auth_payload import TokenPayload

logger = logging.getLogger(__name__)

class InternoCoreGlobalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 0. CORS EXEMPTION (Preflight HARDENING)
        # If CORSMiddleware is outer, it should handle preflights. 
        # If it reaches here, we ensure we don't block OPTIONS even if they are malformed.
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path.lower()
        transaction_id = request.headers.get("X-Trace-Id") or \
                         request.headers.get("X-Correlation-ID") or \
                         request.headers.get("X-Transaction-ID") or \
                         str(uuid.uuid4())
        
        request.state.transaction_id = transaction_id 
        start_time = time.time()
        
        # 1. PUBLIC ROUTES IDENTIFICATION (Improved)
        is_public_route = any(x in path for x in [
            "/auth/login", 
            "/auth/social-login",
            "/auth/select-company",
            "/auth/collaborator",
            "/auth/refresh",
            "/auth/request-password-reset",
            "/auth/confirm-password-reset",
            "/public/register-company",
            "/internal/",
            "/docs", 
            "/openapi.json", 
            "/redoc", 
            "/static", 
            "/health",
            "/api/v1/health",
            "/download/native",
            "/billing/webhook",
            "/favicon.ico"
        ]) or path == "/"

        # 2. TENANT EXTRACTION
        company_id = request.headers.get("X-Company-ID")
        user_id = None
        group_id = None
        
        auth_header = request.headers.get("Authorization")
        token = None
        is_selection = False
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                import base64
                parts = token.split(".")
                if len(parts) == 3:
                    payload_b64 = parts[1]
                    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                    payload_json = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                    payload = payload_json
                    
                    if not company_id and payload.get("company_id"):
                        company_id = payload.get("company_id")
                    
                    user_id = payload.get("sub")
                    group_id = payload.get("group_id")
                    
                    if payload.get("typ") == "selection":
                        is_selection = True
                        request.state.user_token = None
                    else:
                        try:
                            token_payload = TokenPayload(**payload)
                            token_payload.token = token
                            request.state.user_token = token_payload
                        except Exception:
                            pass
            except Exception:
                pass

        # 3. SECURITY BYPASS (GOD MODE / INTERNAL TRUST)
        bypass_tenant = request.headers.get("X-Admin-Master-Key") == "GOD_MODE_ACTIVE"
        
        # 3.2 TENANT CROSS-CHECK (Security Lockdown)
        if not bypass_tenant and not is_public_route:
            # Si no hay company_id en header ni en token (y la ruta no es pública), bloqueamos
            if not company_id:
                logger.error(f"Middleware Security: Missing Company ID for route: {path}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": f"Security Lockdown: X-Company-ID header is REQUIRED for {path}",
                        "meta": {"trace_id": transaction_id}
                    }
                )

            # Validación Cruzada: Si el token trae una empresa, debe coincidir con el header
            if hasattr(request.state, "user_token") and request.state.user_token:
                token_company = getattr(request.state.user_token, "company_id", None)
                if token_company and str(token_company).lower() != str(company_id).lower():
                    logger.error(f"Middleware Security: Tenant Mismatch. Header={company_id}, Token={token_company}, Path={path}")
                    return JSONResponse(
                        status_code=403,
                        content={
                            "status": "error",
                            "message": "Tenant mismatch: Header X-Company-ID does not match Token company_id.",
                            "meta": {"trace_id": transaction_id}
                        }
                    )

            # Restricción de Tokens de Selección (Solo para handshake)
            if is_selection and "/select-company" not in path:
                logger.error(f"Middleware Security: Blocking Selection Token for restricted route. Path={path}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "status": "error",
                        "message": "Security: Selection tokens restricted to handshake phase.",
                        "meta": {"trace_id": transaction_id}
                    }
                )
        token_ctx = None
        if company_id or user_id:
            try:
                company_uuid = None
                if company_id and company_id != "None":
                    company_uuid = uuid.UUID(str(company_id))
                
                group_uuid = None
                if group_id and group_id != "None":
                    group_uuid = uuid.UUID(str(group_id))
                    
                # Extract extended info if token allows
                role_val = "OPERATOR"
                role_names_val = []
                warehouses_val = []
                
                if hasattr(request.state, "user_token") and request.state.user_token:
                    role_val = request.state.user_token.role
                    role_names_val = request.state.user_token.role_names
                    # Ensure warehouses are UUIDs
                    warehouses_val = []
                    for w in request.state.user_token.accessible_warehouses:
                        try:
                            warehouses_val.append(uuid.UUID(str(w)) if not isinstance(w, uuid.UUID) else w)
                        except:
                            continue

                user_ctx = UserContext(
                    company_id=company_uuid, 
                    user_id=str(user_id) if user_id else None,
                    group_id=group_uuid,
                    trace_id=transaction_id,
                    token=token,
                    role=role_val,
                    role_names=role_names_val,
                    accessible_warehouses=warehouses_val
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
            # 5. REQUEST EXECUTION
            response = await call_next(request)
            
            # 6. RESPONSE FORMATTING
            content_type = response.headers.get("content-type", "")
            
            # --- FAST EXIT FOR TECHNICAL ROUTES (Swagger, Redoc, OpenAPI) ---
            # Avoids "Unable to render this definition" by not wrapping the JSON in ApiResponse
            if any(x in path for x in ["/openapi.json", "/docs", "/redoc"]):
                response.headers["X-Transaction-ID"] = transaction_id
                return response

            # --- FAST EXIT FOR NON-JSON ---
            if "application/json" not in content_type:
                response.headers["X-Transaction-ID"] = transaction_id
                return response

            # Processing for all remaining JSON responses
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
                    error_msg = original_data.get("detail", "Error") if isinstance(original_data, dict) else str(original_data)
                    content = ApiResponse(
                        status="success" if is_success else "error",
                        data=original_data if is_success else None,
                        message="Operation completed" if is_success else str(error_msg),
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
            from common.exceptions import DomainException, UnauthorizedException, NotFoundException, BusinessRuleException
            
            if isinstance(e, HTTPException):
                raise e
            
            # --- PHASE 37: Domain Exception Mapping ---
            if isinstance(e, DomainException):
                status_code = 400
                if isinstance(e, (UnauthorizedException)):
                    status_code = 403
                elif isinstance(e, NotFoundException):
                    status_code = 404
                
                return JSONResponse(
                    status_code=status_code,
                    content={
                        "status": "error",
                        "message": str(e),
                        "meta": {
                            "trace_id": transaction_id,
                            "details": getattr(e, 'details', {})
                        }
                    }
                )

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