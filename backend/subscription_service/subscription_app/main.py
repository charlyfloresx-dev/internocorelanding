from common.security.cors_setup import setup_cors
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from subscription_app.api.v1.endpoints import internal, admin, billing, wallet
from common.infrastructure.database import get_db as get_db

from fastapi.middleware.cors import CORSMiddleware
from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware
from common.security.limiter import limiter
from slowapi.errors import RateLimitExceeded
from subscription_app.core.scheduler import start_scheduler
import stripe

app = FastAPI(
    title="Interno Core - Subscription Service",
    description="Microservicio de Suscripciones, Entitlements y Licenciamiento",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_middleware(InternoCoreGlobalMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"status": "error", "message": "Límite de solicitudes excedido. Por favor, espera un momento.", "meta": {"code": "RATE_LIMIT_EXCEEDED"}}
    )

# Configuración de CORS
setup_cors(app)

# Rutas
app.include_router(internal.router, prefix="/internal", tags=["Internal"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(wallet.router, prefix="/api/v1/wallet", tags=["Wallet Kiosk"])

@app.on_event("startup")
async def startup_event():
    # 1. Start Scheduler
    start_scheduler()
    print("🚀 Scheduler iniciado: Auditoría de almacenamiento activa.")

    # 2. Stripe Connectivity Check
    if settings.stripe.int_stripe_secret_key:
        try:
            stripe.api_key = settings.stripe.int_stripe_secret_key
            # Validar conexión mínima (sin filtrar por cuenta si es test mode global)
            stripe.Account.retrieve()
            print("💳 Stripe: Conexión validada exitosamente.")
        except Exception as e:
            print(f"⚠️ Stripe Error: No se pudo validar la conexión. {str(e)}")
    else:
        print("⚠️ Stripe: CORE_STRIPE_SECRET_KEY no configurada.")

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "service": "subscription_service", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Database connection failed", "details": str(e)}
        )
