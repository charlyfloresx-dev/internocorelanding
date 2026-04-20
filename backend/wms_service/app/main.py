from common.security.cors_setup import setup_cors
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from common.middleware import InternoCoreGlobalMiddleware

from common.config import settings

app = FastAPI(
    title="WMS Service", 
    version="1.0.0",
    openapi_version="3.0.2",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(InternoCoreGlobalMiddleware)

setup_cors(app)

# Registrar Routers Centralizados
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "wms_service"}