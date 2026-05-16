import asyncio
import sys
import logging
from logging.config import dictConfig
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from hcm_app.core.database import engine
from hcm_app.models import Base
from hcm_app.api.v1.api import api_router

from common.middleware import InternoCoreGlobalMiddleware
from common.security.cors_setup import setup_cors

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


async def wait_for_db(engine, max_tries=10, wait_seconds=3):
    from sqlalchemy.future import select
    for i in range(1, max_tries + 1):
        try:
            logger.info(f"Intentando conectar a hr_db (intento {i}/{max_tries})...")
            async with engine.connect() as conn:
                await conn.execute(select(1))
            logger.info("Conexion a hr_db establecida.")
            return True
        except Exception as e:
            logger.error(f"Fallo conexion: {e}")
            if i < max_tries:
                await asyncio.sleep(wait_seconds)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando InternoCore HR-Service...")
    if not await wait_for_db(engine):
        sys.exit(1)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    #     logger.info("Esquema HR sincronizado.")
    yield
    logger.info("Apagando HR-Service.")


app = FastAPI(
    title="InternoCore HR-Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# ── Phase 50: Security & Governance Middleware ──
# Decondes JWT and sets request.state.user_token for SubscriptionGuard
app.add_middleware(InternoCoreGlobalMiddleware)

# CORS setup for frontend communication
setup_cors(app)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content={
            "status": "error",
            "message": exc.detail,
            "meta": {},
        },
    )


@app.get("/", tags=["Health"])
async def health():
    return {"status": "online", "service": "hr-service", "version": "1.0.0"}
