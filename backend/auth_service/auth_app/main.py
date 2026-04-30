from auth_app.core.config import settings  # AWS SECRETS MUST LOAD FIRST
from common.security.cors_setup import setup_cors
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
from slowapi.errors import RateLimitExceeded
from common.security.limiter import limiter

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
from auth_app.core.database import engine, AsyncSessionLocal
from auth_app.models import Base, User

# Estructura del sistema Interno Core
from common.responses import ApiResponse
from auth_app.api.v1.api import api_router
from auth_app.api.v2.api import api_router as v2_api_router

# Middlewares
from common.middleware import InternoCoreGlobalMiddleware
from auth_app.core.middleware import TenantSecurityMiddleware, BlacklistMiddleware

async def wait_for_db_connection(engine, max_tries=10, wait_seconds=3):
    for i in range(1, max_tries + 1):
        try:
            logger.info(f"Intentando conectar a la DB (intento {i}/{max_tries})...")
            async with engine.connect() as conn:
                await conn.execute(select(1))
            logger.info("Conexion a la DB establecida.")
            return True
        except Exception as e:
            logger.error(f"Fallo conexion a la DB: {e}")
            if i < max_tries:
                await asyncio.sleep(wait_seconds)
    return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando InternoCore Auth-Service...")
    if not await wait_for_db_connection(engine):
        sys.exit(1)
    
    async with engine.begin() as conn:
        logger.info("Sincronizando esquema de base de datos...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Esquema sincronizado.")

    yield
    logger.info("Apagando InternoCore Auth-Service...")

# --- INSTANCIA DE FASTAPI ---
app = FastAPI(
    title="InternoCore Auth-Service",
    version="2.1.0",
    lifespan=lifespan,
    # Sincronizamos con las excepciones del middleware
    docs_url="/docs",
    openapi_url="/openapi.json"
)
app.state.limiter = limiter

# --- MIDDLEWARES (Orden: El último añadido es el primero en ejecutarse) ---

# 4. Global Middleware (Formateo, Tracing y Seguridad de Tenant Unificada)
app.add_middleware(InternoCoreGlobalMiddleware)

# 2. CORS (DEBE SER EL ÚLTIMO EN AÑADIRSE PARA SER EL PRIMERO EN PROCESAR PREFLIGHTS)
setup_cors(app)

# --- RUTAS ---
app.include_router(api_router, prefix="/api/v1")
app.include_router(v2_api_router, prefix="/api/v2")

# --- MANEJO DE ERRORES ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    trace_id = getattr(request.state, "transaction_id", "not-available")
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={
            "status": "error",
            "message": exc.detail,
            "meta": {"trace_id": trace_id}
        }
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    trace_id = getattr(request.state, "transaction_id", "not-available")
    # Usamos la clase ApiResponse.error para mantener consistencia con el ecosistema
    response = ApiResponse.error(
        message="Has superado el límite de intentos permitidos. Por favor, espera un momento.",
        code="RATE_LIMIT_EXCEEDED",
        trace_id=trace_id,
        data={"limit": exc.detail}
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=response.model_dump()
    )

@app.get("/", tags=["Health"])
async def read_root():
    return {"status": "online", "service": "auth-service", "version": "2.1.0"}
