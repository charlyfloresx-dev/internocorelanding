from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware
from common.models import Base
from app.db.session import engine
from app.api.v1.endpoints import transactions, reconciliation, boms
from app.models import inventory  # Ensure models are imported for Base.metadata
from app.core.workers.reconciliation_worker import ReconciliationWorker
from app.core.workers.transit_worker import TransitAgeWorker

worker = ReconciliationWorker(interval_seconds=300) # 5 minutes heart-beat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas al iniciar (Solo para desarrollo)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start Background Workers
    import asyncio
    asyncio.create_task(worker.start())
    
    transit_worker = TransitAgeWorker(interval_seconds=3600)
    asyncio.create_task(transit_worker.start())
    
    yield
    # Stop workers
    await worker.stop()
    await transit_worker.stop()

app = FastAPI(
    title="InternoCore Inventory-Service",
    description="Microservicio Core para Inventario y Kardex",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuración de CORS basada en InternoSettings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.int_backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(InternoCoreGlobalMiddleware)

from app.api.v1.endpoints import transactions, dashboard, search

# Registro de Routers (Uso de /internal para facilitar gobernanza)
app.include_router(transactions.router, prefix="/api/v1/inventory", tags=["Inventory Transactions (Kardex)"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Variant Awareness Search"])
app.include_router(reconciliation.router, prefix="/api/v1/inventory", tags=["Reconciliation & Self-Healing"])
app.include_router(boms.router, prefix="/api/v1/inventory/boms", tags=["BOM Management"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Stock Audit Dashboard"])

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "inventory-service"}

@app.get("/")
async def root():
    return {"message": "InternoCore Inventory-Service Online"}
