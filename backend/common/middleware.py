import uuid
import time
import json
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.concurrency import iterate_in_threadpool
from common.responses import ApiResponse, ApiMeta

class InternoCoreGlobalMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 1. EXCLUIR RUTAS DE DOCUMENTACIÓN Y SISTEMA
        path = request.url.path
        if path in ["/docs", "/redoc", "/openapi.json"] or path.startswith("/static"):
            return await call_next(request)

        # 2. SEGUIMIENTO DE TRANSACCIÓN
        transaction_id = request.headers.get("X-Transaction-ID", str(uuid.uuid4()))
        request.state.transaction_id = transaction_id 
        start_time = time.time()
        
        try:
            response = await call_next(request)
            content_type = response.headers.get("content-type", "")
            
            # Solo procesamos si es JSON
            if "application/json" not in content_type:
                response.headers["X-Transaction-ID"] = transaction_id
                return response

            # Capturamos el cuerpo de la respuesta original
            response_body = [section async for section in response.body_iterator]
            response_body_bytes = b"".join(response_body)
            
            try:
                original_data = json.loads(response_body_bytes.decode())
                
                # Caso A: La respuesta ya viene formateada con ApiResponse
                if isinstance(original_data, dict) and "status" in original_data and "meta" in original_data:
                    content = original_data
                    if content.get("meta"):
                        content["meta"]["latency"] = f"{time.time() - start_time:.4f}s"
                        content["meta"]["trace_id"] = transaction_id
                
                # Caso B: Homologar respuestas planas o de error de FastAPI al estándar
                else:
                    is_success = 200 <= response.status_code < 300
                    
                    # Usamos el modelo ApiResponse de common.responses para asegurar consistencia [cite: 2026-01-20]
                    content = ApiResponse(
                        status="success" if is_success else "error",
                        data=original_data if is_success else None,
                        message="Operación completada" if is_success else str(original_data.get("detail", "Error de servidor")),
                        meta=ApiMeta(
                            trace_id=transaction_id,
                            latency=f"{time.time() - start_time:.4f}s"
                        )
                    ).model_dump(exclude_none=False) # Mantenemos 'data' aunque sea None para el frontend

                new_headers = dict(response.headers)
                new_headers.pop("content-length", None) 
                new_headers["X-Transaction-ID"] = transaction_id

                return JSONResponse(
                    status_code=response.status_code, 
                    content=content, 
                    headers=new_headers
                )

            except Exception:
                # Si falla el parseo JSON, devolvemos la respuesta original intacta
                response.headers["X-Transaction-ID"] = transaction_id
                response.body_iterator = iterate_in_threadpool(iter([response_body_bytes]))
                return response

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            # Error crítico en el middleware
            return JSONResponse(
                status_code=500, 
                content={
                    "status": "error", 
                    "message": f"Middleware Error: {str(e)}",
                    "meta": {"trace_id": transaction_id}
                }
            )