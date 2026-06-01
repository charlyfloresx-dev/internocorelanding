from common.security.cors_setup import setup_cors
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from wms_app.api.v1.api import api_router
from common.middleware import InternoCoreGlobalMiddleware
from common.security.limiter import limiter
from slowapi.errors import RateLimitExceeded

from common.config import settings

app = FastAPI(
    title="WMS Service",
    version="1.0.0",
    openapi_version="3.0.2",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json"
)

app.state.limiter = limiter
app.add_middleware(InternoCoreGlobalMiddleware)
setup_cors(app)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"status": "error", "message": "Límite de solicitudes excedido. Por favor, espera un momento.", "meta": {"code": "RATE_LIMIT_EXCEEDED"}}
    )

# Registrar Routers Centralizados
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "wms_service"}
