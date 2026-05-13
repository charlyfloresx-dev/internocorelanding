import os
import sys
import asyncio
import logging
import uuid
from decimal import Decimal

# Setup paths
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in [BACKEND_ROOT, SERVICE_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select

from app.models.package import TravelPackage
from app.models.group import TravelerGroup
from common.models import Base

# Environment-aware DB URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback for Host-based execution (mapping container 5432 to host 5433)
    DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5433/viatra_db"

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Standard Demo IDs (Synced with Auth Service)
ENTERPRISE_ID = uuid.UUID("9cd9986b-89da-48b7-8733-26a2a1225b01")
LOGISTICS_ID  = uuid.UUID("ad6cc8a6-34f9-42df-8f29-28254e0ad242")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_viatra")

async def run_seed():
    logger.info(f"🚀 Viatra Seed Initialization (DB: {DATABASE_URL.split('@')[-1]})")

    async with engine.begin() as conn:
        logger.info("🛠️  Syncing Viatra Schema...")
        await conn.run_sync(Base.metadata.create_all)

        # Using direct SQL with ON CONFLICT for absolute idempotency and avoiding ORM session overhead during boot
        logger.info("📦 Seeding Traveler Packages...")
        
        # InternoCorp Package
        p1_id = uuid.UUID("86699317-09d9-48e0-8733-111111111111")
        await conn.execute(text("""
            INSERT INTO viatra_travel_packages (id, company_id, tenant_id, name, destination, total_price_amount, total_price_currency, max_capacity, is_active, version_id, created_at)
            VALUES (:id, :cid, :tid, :name, :dest, :amt, :curr, :cap, true, 1, NOW())
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": p1_id, "cid": ENTERPRISE_ID, "tid": ENTERPRISE_ID,
            "name": "Mission: Control Center Houston", "dest": "Houston, TX",
            "amt": Decimal("2500.00"), "curr": "USD", "cap": 50
        })

        # Logistics Package
        p2_id = uuid.UUID("ad6cc8a6-1111-42df-8f29-222222222222")
        await conn.execute(text("""
            INSERT INTO viatra_travel_packages (id, company_id, tenant_id, name, destination, total_price_amount, total_price_currency, max_capacity, is_active, version_id, created_at)
            VALUES (:id, :cid, :tid, :name, :dest, :amt, :curr, :cap, true, 1, NOW())
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": p2_id, "cid": LOGISTICS_ID, "tid": LOGISTICS_ID,
            "name": "Logistics Hub Summit 2026", "dest": "Panamá City, PAN",
            "amt": Decimal("1250.00"), "curr": "USD", "cap": 100
        })

        logger.info("👥 Seeding Traveler Groups...")
        
        # Group 1
        await conn.execute(text("""
            INSERT INTO viatra_traveler_groups (id, company_id, tenant_id, name, package_id, leader_name, status, is_active, version_id, created_at)
            VALUES (:id, :cid, :tid, :name, :pid, :leader, 'CONFIRMED', true, 1, NOW())
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": uuid.UUID("69aa5ddc-1111-46e6-a7f0-333333333333"),
            "cid": ENTERPRISE_ID, "tid": ENTERPRISE_ID,
            "name": "InternoCorp Alpha Squad", "pid": p1_id, "leader": "Charly Flores"
        })

        # Group 2
        await conn.execute(text("""
            INSERT INTO viatra_traveler_groups (id, company_id, tenant_id, name, package_id, leader_name, status, is_active, version_id, created_at)
            VALUES (:id, :cid, :tid, :name, :pid, :leader, 'PENDING', true, 1, NOW())
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": uuid.UUID("74125896-2222-4bc1-bbaa-444444444444"),
            "cid": LOGISTICS_ID, "tid": LOGISTICS_ID,
            "name": "Logistics Fleet Gamma", "pid": p2_id, "leader": "Sentinel Support"
        })

    logger.info("✅ Viatra Service Seed COMPLETED (SQL Mode).")




if __name__ == "__main__":
    asyncio.run(run_seed())
