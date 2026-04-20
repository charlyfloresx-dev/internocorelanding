import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import photos, payments, onboarding, staff
from app.print_worker import print_worker_loop
from app.core.database import create_tables

app = FastAPI(title="Interno Core - Kiosk Service")

@app.on_event("startup")
async def startup_event():
    # 1. Auto-crear tablas en la DB (modo Edge — sin Alembic)
    await create_tables()
    # 2. Lanzar print worker daemon en el background del event loop
    asyncio.create_task(print_worker_loop())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Expandir si es necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(photos.router, prefix="/api/v1/kiosk/photos", tags=["Kiosk Photos"])
app.include_router(payments.router, prefix="/api/v1/kiosk/payments", tags=["Kiosk Payments"])
app.include_router(onboarding.router, prefix="/api/v1/kiosk/onboarding", tags=["Kiosk Onboarding"])
app.include_router(staff.router, prefix="/api/v1/kiosk/staff", tags=["Staff Operations"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "kiosk"}
