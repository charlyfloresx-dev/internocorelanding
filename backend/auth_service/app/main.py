import asyncio
import uuid
import time
import sys
import logging
from logging.config import dictConfig
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# --- CONFIGURACIÓN DE LOGGING ---
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "INFO", "propagate": True},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"level": "INFO"},
    },
}
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Imports de base de datos y modelos
from app.core.database import engine, AsyncSessionLocal
from app.models import Base, User

# Estructura del sistema Interno Core
from common.responses import ApiResponse
from app.api.v1.api import api_router
from app.api.v2.api import api_router as v2_api_router
from app.core.config import settings

# Middlewares
from common.middleware import InternoCoreGlobalMiddleware
from app.core.middleware import TenantSecurityMiddleware, BlacklistMiddleware

async def wait_for_db_connection(engine, max_tries=10, wait_seconds=3):
    for i in range(1, max_tries + 1):
        try:
            logger.info(f"⏳ Intentando conectar a la DB (intento {i}/{max_tries})...")
            async with engine.connect() as conn:
                await conn.execute(select(1))
            logger.info("✅ Conexión a la DB establecida.")
            return True
        except Exception as e:
            logger.error(f"❌ Falló conexión a la DB: {e}")
            if i < max_tries:
                await asyncio.sleep(wait_seconds)
    return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Iniciando InternoCore Auth-Service...")
    if not await wait_for_db_connection(engine):
        sys.exit(1)
    
    async with engine.begin() as conn:
        logger.info("🔍 Sincronizando esquema de base de datos...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Esquema sincronizado.")

    logger.info("Verificando existencia de usuarios...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        if not result.scalars().first():
            logger.warning("⚠️ Base de datos vacía. Se recomienda ejecutar scripts/seed.py manualmente si el CMD falló.")
        else:
            logger.info("ℹ️ Base de datos ya poblada.")

    yield
    logger.info("🛑 Apagando InternoCore Auth-Service...")

# --- INSTANCIA DE FASTAPI ---
app = FastAPI(
    title="InternoCore Auth-Service",
    version="2.1.0",
    lifespan=lifespan,
    # Sincronizamos con las excepciones del middleware
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# --- MIDDLEWARES (Orden: De afuera hacia adentro) ---

# 1. CORS (Siempre el primero para peticiones del navegador)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True, 
        allow_methods=["*"], 
        allow_headers=["*", "x-company-id", "x-selection-token", "authorization", "x-transaction-id"],
        expose_headers=["x-selection-token", "x-company-id"],
    )

# 2. Global Middleware (Formateo y bypass de rutas públicas)
app.add_middleware(InternoCoreGlobalMiddleware)

# 3. Seguridad de Negocio (Solo se ejecutan si el Global Middleware da paso)
app.add_middleware(BlacklistMiddleware)
app.add_middleware(TenantSecurityMiddleware)

# --- RUTAS ---
app.include_router(api_router, prefix="/api/v1")
app.include_router(v2_api_router, prefix="/api/v2")

# --- MANEJO DE ERRORES ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    trace_id = getattr(request.state, "transaction_id", "not-available")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "meta": {"trace_id": trace_id}
        }
    )

@app.get("/", tags=["Health"])
async def read_root():
    return {"status": "online", "service": "auth-service", "version": "2.1.0"}