import uuid
import logging
import time
import json
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.concurrency import iterate_in_threadpool
from common.responses import ApiResponse, ApiMeta
from common.context import request_context
from common.domain.entities.user_context import UserContext
from common.security.auth_payload import TokenPayload
from common.config import settings as _settings

logger = logging.getLogger(__name__)

class InternoCoreEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        if isinstance(obj, (time.struct_time,)):
            return time.strftime('%Y-%m-%d %H:%M:%S', obj)
        import datetime
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        from decimal import Decimal
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

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
            "/admin/elevate",        # break-glass pre-auth — no JWT ni company_id requeridos
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
            "/whatsapp/webhook",
            "/favicon.ico",
            "/ws/"
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
        # Usar settings para comparar — nunca hardcodear la clave en el middleware
        bypass_tenant = (
            bool(request.headers.get("X-Admin-Master-Key"))
            and request.headers.get("X-Admin-Master-Key") == _settings.int_admin_master_key
        )
        
        # 3.2 TENANT CROSS-CHECK (Security Lockdown)
        if not bypass_tenant and not is_public_route:
            # Si no hay company_id en header ni en token (y la ruta no es pública), bloqueamos
            if not company_id:
                logger.error(f"Middleware Security: Missing Company ID for route: {path}")
                return Response(
                    status_code=400,
                    content=json.dumps({
                        "status": "error",
                        "message": f"Security Lockdown: X-Company-ID header is REQUIRED for {path}",
                        "meta": {"trace_id": transaction_id}
                    }, cls=InternoCoreEncoder),
                    media_type="application/json"
                )

            # Validación Cruzada: Si el token trae una empresa, debe coincidir con el header
            if hasattr(request.state, "user_token") and request.state.user_token:
                token_company = getattr(request.state.user_token, "company_id", None)
                if token_company and str(token_company).lower() != str(company_id).lower():
                    logger.error(f"Middleware Security: Tenant Mismatch. Header={company_id}, Token={token_company}, Path={path}")
                    return Response(
                        status_code=403,
                        content=json.dumps({
                            "status": "error",
                            "message": "Tenant mismatch: Header X-Company-ID does not match Token company_id.",
                            "meta": {"trace_id": transaction_id}
                        }, cls=InternoCoreEncoder),
                        media_type="application/json"
                    )

            # Restricción de Tokens de Selección (Solo para handshake)
            if is_selection and "/select-company" not in path:
                logger.error(f"Middleware Security: Blocking Selection Token for restricted route. Path={path}")
                return Response(
                    status_code=403,
                    content=json.dumps({
                        "status": "error",
                        "message": "Security: Selection tokens restricted to handshake phase.",
                        "meta": {"trace_id": transaction_id}
                    }, cls=InternoCoreEncoder),
                )

            # 3.3. PHASE 19: GRACE PERIOD & DEGRADATION (Capa 7 Lockdown)
            if hasattr(request.state, "user_token") and request.state.user_token:
                sub_status = getattr(request.state.user_token, "status", "ACTIVE")
                is_readonly = getattr(request.state.user_token, "readonly", False)
                is_billing_route = "/billing" in path

                if not is_billing_route:
                    # Bloqueo total para UNPAID o CANCELED
                    if sub_status in ["UNPAID", "CANCELED"]:
                        logger.warning(f"Middleware Security: Access Blocked for UNPAID/CANCELED subscription. Path={path}")
                        return Response(
                            status_code=402,
                            content=json.dumps({
                                "status": "error",
                                "message": "Subscription Unpaid. Full access blocked. Please update payment method.",
                                "meta": {"trace_id": transaction_id}
                            }, cls=InternoCoreEncoder),
                            media_type="application/json"
                        )
                    
                    # Bloqueo parcial (Solo Lectura) para RESTRICTED o flag readonly
                    if (sub_status == "RESTRICTED" or is_readonly) and request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                        logger.warning(f"Middleware Security: Write Access Blocked (RESTRICTED/readonly). Path={path}, Method={request.method}")
                        return Response(
                            status_code=402,
                            content=json.dumps({
                                "status": "error",
                                "message": "Subscription Restricted (Read-Only Mode). Payment Required for write operations.",
                                "meta": {"trace_id": transaction_id}
                            }, cls=InternoCoreEncoder),
                            media_type="application/json"
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
                role_val = "GOD_MODE_ADMIN" if bypass_tenant else "OPERATOR"
                role_names_val = ["admin"] if bypass_tenant else []
                warehouses_val = []
                
                if hasattr(request.state, "user_token") and request.state.user_token:
                    # Priority: GOD_MODE_ADMIN > Token Role
                    if role_val != "GOD_MODE_ADMIN":
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
                    sub=str(user_id) if user_id else None,
                    group_id=group_uuid,
                    trace_id=transaction_id,
                    token=token,
                    role=role_val,
                    role_names=role_names_val,
                    accessible_warehouses=warehouses_val,
                    readonly=is_readonly if 'is_readonly' in locals() else False,
                    scopes=getattr(request.state.user_token, "scopes", []) if hasattr(request.state, "user_token") and request.state.user_token else [],
                    status=getattr(request.state.user_token, "status", "ACTIVE") if hasattr(request.state, "user_token") and request.state.user_token else "ACTIVE"
                )
                token_ctx = request_context.set(user_ctx)
            except (ValueError, TypeError):
                if company_id:
                    return Response(
                        status_code=400,
                        content=json.dumps({
                            "status": "error",
                            "message": f"X-Company-ID header must be a valid UUID (Got: {company_id})",
                            "meta": {"trace_id": transaction_id}
                        }, cls=InternoCoreEncoder),
                        media_type="application/json"
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
                    current_status = getattr(response, "status_code", 500)
                    is_success = 200 <= current_status < 300
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

                # Use custom encoder to handle UUIDs and other non-serializable objects
                json_content = json.dumps(content, cls=InternoCoreEncoder)

                return Response(
                    status_code=getattr(response, "status_code", 500), 
                    content=json_content, 
                    headers=new_headers,
                    media_type="application/json"
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
                status_code = getattr(e, 'status_code', 400)
                logger.warning(f"DOMAIN_EXCEPTION_CAUGHT: {type(e).__name__} - {str(e)} (trace:{transaction_id})")
                
                return Response(
                    status_code=status_code,
                    content=json.dumps({
                        "status": "error",
                        "message": str(e),
                        "meta": {
                            "trace_id": transaction_id,
                            "code": getattr(e, 'code', "INTERNAL_DOMAIN_ERROR"),
                            "details": getattr(e, 'details', {})
                        }
                    }, cls=InternoCoreEncoder),
                    media_type="application/json"
                )

            import traceback
            traceback.print_exc()
            
            return Response(
                status_code=500, 
                content=json.dumps({
                    "status": "error", 
                    "message": f"Critical Middleware Error: {str(e)}",
                    "meta": {"trace_id": transaction_id}
                }, cls=InternoCoreEncoder),
                media_type="application/json"
            )
        finally:
            if token_ctx:
                request_context.reset(token_ctx)