from common.security.cors_setup import setup_cors
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware
from common.models import Base
from inventory_app.db.session import engine
from inventory_app.api.v1.endpoints import transactions, reconciliation, boms, inter_company_transfers
from inventory_app.models import inventory  # Ensure models are imported for Base.metadata
from inventory_app.models import inter_company_transfer  # ICT model - ensures table creation
from inventory_app.core.workers.reconciliation_worker import ReconciliationWorker
from inventory_app.core.workers.transit_worker import TransitAgeWorker

worker = ReconciliationWorker(interval_seconds=300) # 5 minutes heart-beat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Audit
    from inventory_app.core.events import setup_audit_listeners
    setup_audit_listeners()

    # Las tablas ahora se gestionan via Alembic en el entrypoint.sh 
    
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

# 2. Global Middleware
app.add_middleware(InternoCoreGlobalMiddleware)

# 1. CORS (DEBE SER EL ÚLTIMO EN AÑADIRSE PARA SER EL PRIMERO EN PROCESAR PREFLIGHTS)


setup_cors(app)

from inventory_app.api.v1.endpoints import (
    transactions, 
    reconciliation, 
    boms, 
    dashboard, 
    inventory_search, 
    dashboard_consolidated,
    demo_reset,
    onboarding,
    inventory,
    customs,
    variants
)

# Registro de Routers
# Prefix matches the environment.ts configurations for consistency
app.include_router(customs.router, prefix="/api/v1/customs", tags=["Customs Compliance (Anexo 24)"])
app.include_router(transactions.router, prefix="/api/v1/inventory", tags=["Inventory Transactions (Kardex)"])
app.include_router(inventory_search.router, prefix="/api/v1/search", tags=["Variant Awareness Search"])
app.include_router(reconciliation.router, prefix="/api/v1/inventory", tags=["Reconciliation & Self-Healing"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory Operations"])
app.include_router(boms.router, prefix="/api/v1/inventory/boms", tags=["BOM Management"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Stock Audit Dashboard"])
app.include_router(onboarding.router, prefix="/api/v1", tags=["Onboarding / Readiness"])
app.include_router(demo_reset.router, prefix="/api/v1", tags=["Admin / Demo"])
app.include_router(
    inter_company_transfers.router,
    prefix="/api/v1/inventory/transfers/inter-company",
    tags=["Inter-Company Transfers (Trusted Broker)"]
)
app.include_router(variants.router, prefix="/api/v1/inventory", tags=["Industrial Variants (Supplier Mappings)"])


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "inventory-service"}

@app.get("/")
async def root():
    return {"message": "InternoCore Inventory-Service Online"}
