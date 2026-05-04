from common.security.cors_setup import setup_cors
from fastapi import FastAPI
from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware
from cmms_app.routers import asset_routes, tool_routes, work_order_routes, storage_routes

app = FastAPI(
    title="InternoCore CMMS Service",
    description="Assets & Maintenance Management — CMMS industrial multitenant",
    version="1.0.0",
)

# CORS
setup_cors(app)

# Global middleware (JWT extraction, tenant context, audit)
app.add_middleware(InternoCoreGlobalMiddleware)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "cmms_service"}


# ── Routers ────────────────────────────────────────────────────────────────────
api_v1_prefix = getattr(settings, "int_api_v1_str", "/api/v1")

app.include_router(asset_routes.router,      prefix=f"{api_v1_prefix}/assets")
app.include_router(tool_routes.router,       prefix=f"{api_v1_prefix}/tools")
app.include_router(work_order_routes.router, prefix=f"{api_v1_prefix}/work-orders")
app.include_router(storage_routes.router,    prefix=f"{api_v1_prefix}/storage")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cmms_app.main:app", host="0.0.0.0", port=8000, reload=True)
