"""
Asset Manager Service — Main FastAPI Application

Puerto: 8006
Prefijo base: /api/v1
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from asset_app.core.config import settings
from asset_app.core.database import init_db
from asset_app.api.v1.router import api_router
from common.security.cors_setup import setup_cors
from common.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar el servicio."""
    logger.info(f"🚀 {settings.PROJECT_NAME} iniciando en puerto {settings.SERVICE_PORT}...")
    await init_db()
    logger.info("✅ Base de datos inicializada correctamente.")
    yield
    logger.info("🛑 Asset Manager Service apagado.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Motor de Inteligencia Inmobiliaria para Activos en Problemas (Distressed Real Estate Assets). "
        "Evalúa predios catastrales de Tijuana con métricas financieras automáticas y pipeline Kanban."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
setup_cors(app)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }
