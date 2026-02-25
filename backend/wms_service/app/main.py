from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import inventory

app = FastAPI(
    title="WMS Service", 
    version="1.0.0",
    openapi_version="3.0.2",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json"
)

# Habilitar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Origen del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "x-company-id", "x-selection-token", "authorization"],
)

# Registrar Routers
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "wms_service"}