import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.dependencies import get_current_user_payload

# Importaciones ajustadas a tus archivos reales
# Asegúrate de que categories.py exista en la carpeta endpoints
from app.api.v1.endpoints import products, uom_router, categories, brands
from common.exceptions import DomainException

app = FastAPI(
    title="Master Data Service",
    version="1.0.0",
    description="Single Source of Truth for Products, UOMs, and Business Partners."
)

# Leer orígenes permitidos desde variable de entorno (CSV)
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# 1. Configuración de Seguridad (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handler para excepciones de dominio (Clean Architecture)
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message, "status": "error"}
    )

# 2. Registro de Rutas Protegidas (Multitenancy)
# Todas comparten la dependencia get_current_user para validar el tenant_id a nivel de API

# Módulo de Productos
app.include_router(
    products.router,
    prefix="/api/v1/products",
    tags=["Products"],
    dependencies=[Depends(get_current_user_payload)]
)

# Módulo de Unidades de Medida (UOM)
# Usamos uom_router que es el archivo que creaste
app.include_router(
    uom_router.router,
    prefix="/api/v1/ums",
    tags=["Units of Measure"],
    dependencies=[Depends(get_current_user_payload)]
)

# Módulo de Categorías
app.include_router(
    categories.router,
    prefix="/api/v1/categories",
    tags=["Product Categories"],
    dependencies=[Depends(get_current_user_payload)]
)

# Módulo de Marcas
app.include_router(
    brands.router,
    prefix="/api/v1/brands",
    tags=["Product Brands"],
    dependencies=[Depends(get_current_user_payload)]
)

# 3. Endpoints de Sistema
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "master_data_service",
        "version": "1.0.0"
    }