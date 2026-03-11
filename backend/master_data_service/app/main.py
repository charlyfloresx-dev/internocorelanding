import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware

# Routers
from app.api.v1.endpoints.products import router as product_router
from app.api.v1.endpoints import uom_router
from app.api.v1.endpoints import categories
from app.api.v1.endpoints import brands


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seeding is handled by the Dockerfile CMD (scripts/seed.py) before uvicorn starts.
    print("🚀 Master Data Service starting...")
    yield
    print("Application shutdown.")



app = FastAPI(
    title="Master Data Service",
    description="Single Source of Truth for Products, UOMs, and Business Partners.",
    version="1.0.0",
    lifespan=lifespan
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

@app.get("/health")
async def health():
    return {"status": "ok", "service": "master-data-service"}

app.include_router(product_router, prefix="/api/v1/products", tags=["Products"])
app.include_router(uom_router.router, prefix="/api/v1/uoms", tags=["UOMs"])
app.include_router(uom_router.router, prefix="/api/v1/ums", tags=["UOMs"], include_in_schema=False)
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categories"])
app.include_router(brands.router, prefix="/api/v1/brands", tags=["Brands"])