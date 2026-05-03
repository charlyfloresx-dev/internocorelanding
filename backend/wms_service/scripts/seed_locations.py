"""
seed_locations.py
-----------------
[Phase 83] Seeds the demo warehouse with an industrial location layout.

Layout:
  - 3 Virtual zones:  SYS_RECEIVING, SYS_TRANSIT, SYS_QUALITY
  - Aisle 01 (STORAGE): 3 sections x 4 levels x 2 bins = 24 rack slots
  - Aisle 02 (PICKING):  6 positions, velocity A (high-rotation, near shipping)

Run from backend root:
  set CORE_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5433/interno_db
  set PYTHONPATH=backend;backend/inventory_service
  python backend/inventory_service/scripts/flows/seed_locations.py
"""
import asyncio
import os
import sys
import traceback
import uuid
from decimal import Decimal

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from inventory_app.db.session import AsyncSessionLocal
from inventory_app.models.location import InventoryLocation, ZoneType, StorageType
from flows._shared_ids import resolve_flow_ids
from sqlalchemy import select, and_


def make_location(company_id, warehouse_id, code, aisle, section, level, bin_slot,
                  zone_type, storage_type, is_virtual=False, is_multisku=True,
                  max_units=200.0, max_kg=500.0, velocity=None,
                  w=120.0, h=100.0, d=80.0):
    return InventoryLocation(
        id=uuid.uuid4(),
        company_id=company_id,
        tenant_id=company_id,
        warehouse_id=warehouse_id,
        code=code,
        aisle=aisle,
        section=section,
        level=level,
        bin_slot=bin_slot,
        zone_type=zone_type,
        storage_type=storage_type,
        is_virtual=is_virtual,
        is_multisku=is_multisku,
        max_capacity_units=Decimal(str(max_units)),
        max_weight_kg=Decimal(str(max_kg)),
        width_cm=Decimal(str(w)),
        height_cm=Decimal(str(h)),
        depth_cm=Decimal(str(d)),
        current_units=Decimal("0.0"),
        current_weight_kg=Decimal("0.0"),
        velocity_code=velocity,
    )


async def seed_locations():
    print("=" * 60)
    print("SEED: Industrial Location Layout (Phase 83)")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        ids = await resolve_flow_ids(session)
        company_id  = ids["company_id"]
        warehouse_id = ids["warehouse_id"]

        locations = [
            # ── Virtual System Zones ─────────────────────────────────────────
            make_location(company_id, warehouse_id,
                "SYS_RECEIVING", "00", "00", "00", "R",
                ZoneType.RECEIVING, StorageType.DRY,
                is_virtual=True, max_units=9999, max_kg=99999),

            make_location(company_id, warehouse_id,
                "SYS_TRANSIT", "00", "00", "00", "T",
                ZoneType.TRANSIT, StorageType.DRY,
                is_virtual=True, max_units=9999, max_kg=99999),

            make_location(company_id, warehouse_id,
                "SYS_QUALITY", "00", "00", "00", "Q",
                ZoneType.QUALITY, StorageType.DRY,
                is_virtual=True, is_multisku=False, max_units=500, max_kg=2000),

            # ── Aisle 01 — STORAGE ───────────────────────────────────────────
            # 3 sections x 4 levels x 2 bins = 24 rack slots
            *[
                make_location(company_id, warehouse_id,
                    f"01-{sec:02d}-{lvl:02d}-{b}",
                    "01", f"{sec:02d}", f"{lvl:02d}", b,
                    ZoneType.STORAGE, StorageType.DRY,
                    max_units=150, max_kg=400, velocity="B")
                for sec in range(1, 4)
                for lvl in range(1, 5)
                for b in ["A", "B"]
            ],

            # ── Aisle 02 — PICKING (velocity A) ─────────────────────────────
            *[
                make_location(company_id, warehouse_id,
                    f"02-{pos:02d}-01-A",
                    "02", f"{pos:02d}", "01", "A",
                    ZoneType.PICKING, StorageType.DRY,
                    max_units=50, max_kg=100, velocity="A",
                    w=60, h=50, d=40)
                for pos in range(1, 7)
            ],
        ]

        created = 0
        skipped = 0
        for loc in locations:
            existing = await session.execute(
                select(InventoryLocation.id).where(
                    and_(
                        InventoryLocation.company_id == company_id,
                        InventoryLocation.warehouse_id == warehouse_id,
                        InventoryLocation.code == loc.code
                    )
                )
            )
            if existing.scalar() is None:
                session.add(loc)
                created += 1
                print(f"  + {loc.code:20s}  [{loc.zone_type:10s}]  cap={loc.max_capacity_units} pz / {loc.max_weight_kg} kg")
            else:
                skipped += 1

        await session.commit()
        print("-" * 60)
        print(f"OK  Created : {created}")
        print(f"    Skipped : {skipped} (already exist)")
        print(f"    Total   : {len(locations)}")


if __name__ == "__main__":
    try:
        asyncio.run(seed_locations())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
