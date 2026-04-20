from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.routers import booking, payments, sentinel
from app.services.sentinel_engine import SentinelEngine
from app.services.stay_guardian import StayGuardian
from app.core.database import AsyncSessionLocal
from common.middleware import InternoCoreGlobalMiddleware


app = FastAPI(
    title="Viatra Core — Travel Mission Control",
    description="Booking Engine, Document Vault, Fintech Module y Sentinel Bots para gestión de paquetes de viajes grupales.",
    version="0.1.0",
)

app.add_middleware(InternoCoreGlobalMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Routers
app.include_router(booking.router)
app.include_router(payments.router)
app.include_router(sentinel.router)


# Scheduler for SkySentinel
scheduler = AsyncIOScheduler()

async def run_sentinel_job():
    async with AsyncSessionLocal() as session:
        # 1. Flight Pricing
        engine = SentinelEngine(session)
        await engine.check_flights_prices()
        # 2. Hotel Availability
        guardian = StayGuardian(session)
        await guardian.check_hotel_availability()

@app.on_event("startup")
async def startup_event():
    # Flight tracking (6h)
    scheduler.add_job(run_sentinel_job, "interval", hours=6)
    # Hotel tracking (Initial run + 12h cycle)
    # (Simplified: both run in same job or separate jobs, choosing shared for now)
    scheduler.start()

    # Initial run for testing
    await run_sentinel_job()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "viatra_service", "version": "0.1.0"}

