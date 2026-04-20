from app.core.config import settings
from common.security.cors_setup import setup_cors
from app.api.v1.endpoints import scan, dashboard, labor, downtime, work_order, sync, resource, shift
from common.middleware import InternoCoreGlobalMiddleware
from common.error_handlers import domain_exception_handler
from common.exceptions import DomainException
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Exception Handlers
app.add_exception_handler(DomainException, domain_exception_handler)

# Global Middleware (Response Wrapping & Transaction ID)
app.add_middleware(InternoCoreGlobalMiddleware)

# Routers
app.include_router(scan.router, prefix=f"{settings.API_V1_STR}/mes", tags=["MES Scan"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/mes/dashboard", tags=["MES Dashboard"])
app.include_router(labor.router, prefix=f"{settings.API_V1_STR}/mes/labor", tags=["MES Labor"])
app.include_router(downtime.router, prefix=f"{settings.API_V1_STR}/mes/downtime", tags=["MES Downtime"])
app.include_router(work_order.router, prefix=f"{settings.API_V1_STR}/mes/orders", tags=["MES Work Orders"])
app.include_router(sync.router, prefix=f"{settings.API_V1_STR}/mes", tags=["MES Sync"])
app.include_router(resource.router, prefix=f"{settings.API_V1_STR}/mes/resources", tags=["MES Resources"])
app.include_router(shift.router, prefix=f"{settings.API_V1_STR}/mes/shifts", tags=["MES Shifts"])

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
