from mes_app.core.config import settings
from common.security.cors_setup import setup_cors
from mes_app.api.v1.endpoints import (
    scan, dashboard, labor, downtime, work_order, sync, resource,
    shift, planning, production, standard_times, labor_assignment
)
from common.middleware import InternoCoreGlobalMiddleware
from common.error_handlers import domain_exception_handler
from common.exceptions import DomainException
from common.security.limiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.state.limiter = limiter

# Exception Handlers
app.add_exception_handler(DomainException, domain_exception_handler)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"status": "error", "message": "Límite de solicitudes excedido. Por favor, espera un momento.", "meta": {"code": "RATE_LIMIT_EXCEEDED"}}
    )

# Global Middleware (Response Wrapping & Transaction ID)
app.add_middleware(InternoCoreGlobalMiddleware)

# Routers
app.include_router(scan.router, prefix=f"{settings.API_V1_STR}/mes", tags=["MES Scan"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/mes/dashboard", tags=["MES Dashboard"])
app.include_router(labor.router, prefix=f"{settings.API_V1_STR}/mes/labor", tags=["MES Labor"])
app.include_router(labor_assignment.router, prefix=f"{settings.API_V1_STR}/mes/labor", tags=["MES Labor Assignments"])
app.include_router(downtime.router, prefix=f"{settings.API_V1_STR}/mes/downtime", tags=["MES Downtime"])
app.include_router(work_order.router, prefix=f"{settings.API_V1_STR}/mes/orders", tags=["MES Work Orders"])
app.include_router(sync.router, prefix=f"{settings.API_V1_STR}/mes", tags=["MES Sync"])
app.include_router(resource.router, prefix=f"{settings.API_V1_STR}/mes/resources", tags=["MES Resources"])
app.include_router(shift.router, prefix=f"{settings.API_V1_STR}/mes/shifts", tags=["MES Shifts"])
app.include_router(planning.router, prefix=f"{settings.API_V1_STR}/mes/planning", tags=["MES Planning"])
app.include_router(production.router, prefix=f"{settings.API_V1_STR}/mes/production", tags=["MES Production"])
app.include_router(standard_times.router, prefix=f"{settings.API_V1_STR}/mes/standard-times", tags=["MES Standard Times"])

# CORS CloudFront/Frontend
setup_cors(app)

@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Interno Core MES Service is running",
        "meta": {
            "version": "0.1.0",
            "service": "mes_service"
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
