from common.security.cors_setup import setup_cors
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware

# Routers
from master_app.api.v1.endpoints.products import router as product_router
from master_app.api.v1.endpoints.prices import router as prices_router
from master_app.api.v1.endpoints import uom_router
from master_app.api.v1.endpoints import categories
from master_app.api.v1.endpoints import brands
from master_app.api.v1.endpoints import concepts
from master_app.api.v1.endpoints import warehouses
from master_app.api.v1.endpoints.partners import router as partner_router
from master_app.api.v1.endpoints.gis_validator import router as gis_router

# Audit Setup (Moved to lifespan to avoid circular dependencies)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup audit listeners
    from master_app.core.events import setup_audit_listeners
    from master_app.models import Product, Warehouse, MovementConcept, UOMConversion, InventoryLocation
    
    setup_audit_listeners(Product)
    setup_audit_listeners(Warehouse)
    setup_audit_listeners(MovementConcept)
    setup_audit_listeners(UOMConversion)
    setup_audit_listeners(InventoryLocation)

    from master_app.models.product_price import ProductPrice
    setup_audit_listeners(ProductPrice)

    # Seeding is handled by the Dockerfile CMD (scripts/seed.py) before uvicorn starts.
    print("🚀 Master Data Service starting...")
    yield
    print("Application shutdown.")



app = FastAPI(
    title="Master Data Service",
    description="Single Source of Truth for Products, UOMs, and Business Partners.",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# 2. Global Middleware
app.add_middleware(InternoCoreGlobalMiddleware)

# 1. CORS (DEBE SER EL ÚLTIMO EN AÑADIRSE PARA SER EL PRIMERO EN PROCESAR PREFLIGHTS)


setup_cors(app)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "master-data-service"}

app.include_router(product_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(prices_router, prefix="/api/v1/prices", tags=["Product Prices"])
app.include_router(uom_router.router, prefix="/api/v1/uoms", tags=["UOMs"])
app.include_router(uom_router.router, prefix="/api/v1/ums", tags=["UOMs"], include_in_schema=False)
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(brands.router, prefix="/api/v1/brands", tags=["Brands"])
app.include_router(concepts.router, prefix="/api/v1/concepts", tags=["Movement Concepts"])
app.include_router(warehouses.router, prefix="/api/v1/warehouses", tags=["Warehouses"])
app.include_router(partner_router, prefix="/api/v1/partners", tags=["Partners"])
app.include_router(gis_router, prefix="/api/v1/gis", tags=["GIS Property Validation"])

from master_app.api.v1.endpoints import enums as enums_router
app.include_router(enums_router.router, prefix="/api/v1/enums", tags=["System Enums"])

from master_app.api.v1.endpoints import enumerations
app.include_router(enumerations.router, prefix="/api/v1/enumerations", tags=["System Enumerations"])

from master_app.api.v1.endpoints import locations
app.include_router(locations.router, prefix="/api/v1/locations", tags=["Warehouse Structure (SSOT)"])
