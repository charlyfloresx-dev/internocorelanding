import asyncio
from fastapi import FastAPI
from app.api import photos, payments, onboarding, staff
from app.print_worker import print_worker_loop
from app.core.database import create_tables
from common.security.cors_setup import setup_cors

app = FastAPI(title="Interno Core - Kiosk Service")

@app.on_event("startup")
async def startup_event():
    # 1. Auto-crear tablas en la DB (modo Edge — sin Alembic)
    await create_tables()
    # 2. Lanzar print worker daemon en el background del event loop
    asyncio.create_task(print_worker_loop())

setup_cors(app)

app.include_router(photos.router, prefix="/api/v1/kiosk/photos", tags=["Kiosk Photos"])
app.include_router(payments.router, prefix="/api/v1/kiosk/payments", tags=["Kiosk Payments"])
app.include_router(onboarding.router, prefix="/api/v1/kiosk/onboarding", tags=["Kiosk Onboarding"])
app.include_router(staff.router, prefix="/api/v1/kiosk/staff", tags=["Staff Operations"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "kiosk"}
