"""
endpoints/locations.py
-----------------------
[Phase 83] Industrial Location Management Router.

Resolves Bug P0: GET /locations/{code}/density was called by the frontend
Put-Away Handheld component but never implemented in the backend.

Endpoints:
  GET  /inventory/locations                     — List all locations with density semaphore
  GET  /inventory/locations/{code}/density      — P0: Real-time density for a single location
  GET  /inventory/locations/pending-putaway      — Queue of IN movements with location=null
  POST /inventory/locations/seed-demo           — (Dev/Demo) Seed warehouse locations
"""

import uuid
import logging
from typing import List, Optional, Union
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from inventory_app.db.session import get_db
from inventory_app.dependencies.repositories import get_inventory_repository
from inventory_app.domain.repositories.inventory_repository import IInventoryRepository
from inventory_app.models.location import InventoryLocation, ZoneType, StorageType
from common.responses import ApiResponse
from common.security.auth_payload import TokenPayload
from common.security.subscription_guard import SubscriptionGuard

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _location_to_density_dict(loc: InventoryLocation) -> dict:
    """Serializes an InventoryLocation to the density contract the frontend expects."""
    return {
        "location_code":        loc.code,
        "warehouse_id":         str(loc.warehouse_id),
        "aisle":                loc.aisle,
        "section":              loc.section,
        "level":                loc.level,
        "bin_slot":             loc.bin_slot,
        "zone_type":            loc.zone_type,
        "storage_type":         loc.storage_type,
        "is_multisku":          loc.is_multisku,
        "is_virtual":           loc.is_virtual,
        "velocity_code":        loc.velocity_code,
        # Capacity
        "max_capacity":         float(loc.max_capacity_units),
        "max_weight_kg":        float(loc.max_weight_kg),
        # Occupancy (denormalized cache — O(1))
        "current_occupancy":    float(loc.current_units),
        "current_weight_kg":    float(loc.current_weight_kg),
        # Computed
        "available_space":      float(loc.available_space) if loc.available_space is not None else None,
        "utilization_percent":  loc.utilization_percent,
        "density_status":       loc.density_status,      # OK / WARNING / FULL / OVERFLOW / UNLIMITED
    }


# ─── P0: DENSITY ENDPOINT (Bug Fix) ──────────────────────────────────────────

@router.get(
    "/locations/{location_code}/density",
    response_model=ApiResponse,
    summary="[P0] Real-time Density Guard for a specific location",
    tags=["WMS — Location Management"]
)
async def get_location_density(
    location_code: str,
    warehouse_id: uuid.UUID = Query(..., description="Warehouse UUID"),
    repo: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    [Phase 83 — P0 Bug Fix]
    Returns real-time occupancy, capacity, and density semaphore for a location.

    This endpoint was referenced by the PutAway Handheld Component (Step 2) but
    was never implemented — causing a silent failure in the frontend density check.

    Response contract matches exactly what `getLocationDensity()` in inventory.service.ts expects.
    """
    location = await repo.get_location_entity(
        warehouse_id=warehouse_id,
        location_code=location_code.upper(),
        company_id=token.company_id
    )

    if not location:
        # Return an "unlimited" payload for unregistered locations (backwards compatible)
        return ApiResponse(
            status="success",
            data={
                "location_code":       location_code.upper(),
                "warehouse_id":        str(warehouse_id),
                "max_capacity":        0,
                "current_occupancy":   0,
                "available_space":     None,
                "utilization_percent": 0,
                "density_status":      "UNLIMITED",
                "zone_type":           "STORAGE",
                "is_multisku":         True,
                "max_weight_kg":       0,
                "current_weight_kg":   0,
            },
            message="Location not registered — no capacity limits applied."
        )

    return ApiResponse(
        status="success",
        data=_location_to_density_dict(location),
        message="Density data retrieved."
    )


# ─── PENDING PUT-AWAY QUEUE ───────────────────────────────────────────────────

@router.get(
    "/locations/pending-putaway",
    response_model=ApiResponse,
    summary="Queue of IN movements pending physical placement",
    tags=["WMS — Location Management"]
)
async def get_pending_putaway(
    warehouse_id: Optional[uuid.UUID] = Query(None, description="Filter by warehouse"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: IInventoryRepository = Depends(get_inventory_repository),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    [Phase 83] Returns the queue of inventory movements that have been received
    (movement_type=IN) but not yet assigned to a physical rack location
    (location IS NULL or location = 'SYS_RECEIVING').

    Sorted by FIFO (oldest first) to prioritize aged stock.
    Enriched with pedimento_number and days_in_dock for the UI Age Indicator.
    """
    pending = await repo.get_pending_putaway_movements(
        company_id=token.company_id,
        warehouse_id=warehouse_id,
        limit=limit,
        offset=offset
    )

    return ApiResponse(
        status="success",
        data=pending,
        message=f"{len(pending)} movements pending put-away.",
        meta={"count": len(pending), "limit": limit, "offset": offset}
    )


# ─── LIST ALL LOCATIONS ───────────────────────────────────────────────────────

@router.get(
    "/locations",
    response_model=ApiResponse,
    summary="List all locations with real-time density semaphore",
    tags=["WMS — Location Management"]
)
async def list_locations(
    warehouse_id: Optional[uuid.UUID] = Query(None),
    zone_type: Optional[str] = Query(None, description="Filter by zone: RECEIVING, STORAGE, PICKING…"),
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    [Phase 83] Returns all registered locations for a warehouse with their
    real-time density semaphore (uses the denormalized current_units cache for O(1) speed).
    """
    conditions = [InventoryLocation.company_id == token.company_id]
    if warehouse_id:
        conditions.append(InventoryLocation.warehouse_id == warehouse_id)
    if zone_type:
        conditions.append(InventoryLocation.zone_type == zone_type.upper())

    stmt = (
        select(InventoryLocation)
        .where(and_(*conditions))
        .order_by(
            InventoryLocation.aisle,
            InventoryLocation.section,
            InventoryLocation.level,
            InventoryLocation.bin_slot
        )
    )
    result = await db.execute(stmt)
    locations = result.scalars().all()

    return ApiResponse(
        status="success",
        data=[_location_to_density_dict(loc) for loc in locations],
        message=f"{len(locations)} locations found.",
        meta={"count": len(locations)}
    )


# ─── DEMO SEED ────────────────────────────────────────────────────────────────

@router.post(
    "/locations/seed-demo",
    response_model=ApiResponse,
    summary="[Dev/Demo] Seed warehouse locations with industrial layout",
    tags=["WMS — Location Management"]
)
async def seed_demo_locations(
    warehouse_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))
):
    """
    [Phase 83] Seeds the warehouse with a realistic industrial location layout:
    - 3 Virtual system zones (SYS_RECEIVING, SYS_TRANSIT, SYS_QUALITY)
    - Aisle 01: 3 sections × 4 levels × 2 bins = 24 STORAGE slots
    - Aisle 02: 6 PICKING positions (velocity A)
    Idempotent: skips existing locations.
    """
    company_id = token.company_id
    created_count = 0

    def make_loc(code, aisle, section, level, bin_slot,
                 zone, storage, is_virtual=False, multisku=True,
                 max_units=200, max_kg=500, velocity=None,
                 w=120, h=100, d=80):
        return InventoryLocation(
            id=uuid.uuid4(),
            company_id=company_id,
            tenant_id=company_id,
            warehouse_id=warehouse_id,
            code=code,
            aisle=aisle, section=section, level=level, bin_slot=bin_slot,
            zone_type=zone, storage_type=storage,
            is_virtual=is_virtual, is_multisku=multisku,
            max_capacity_units=Decimal(str(max_units)),
            max_weight_kg=Decimal(str(max_kg)),
            width_cm=Decimal(str(w)), height_cm=Decimal(str(h)), depth_cm=Decimal(str(d)),
            current_units=Decimal("0.0"), current_weight_kg=Decimal("0.0"),
            velocity_code=velocity
        )

    locations_to_seed = [
        # ── Virtual Zones ────────────────────────────────────────────────────
        make_loc("SYS_RECEIVING", "00", "00", "00", "R", ZoneType.RECEIVING,
                 StorageType.DRY, is_virtual=True, max_units=9999, max_kg=99999),
        make_loc("SYS_TRANSIT",   "00", "00", "00", "T", ZoneType.TRANSIT,
                 StorageType.DRY, is_virtual=True, max_units=9999, max_kg=99999),
        make_loc("SYS_QUALITY",   "00", "00", "00", "Q", ZoneType.QUALITY,
                 StorageType.DRY, is_virtual=True, multisku=False, max_units=500, max_kg=2000),

        # ── Aisle 01 — STORAGE (3 sections × 4 levels × 2 bins) ─────────────
        *[
            make_loc(f"01-{sec:02d}-{lvl:02d}-{b}",
                     "01", f"{sec:02d}", f"{lvl:02d}", b,
                     ZoneType.STORAGE, StorageType.DRY,
                     max_units=150, max_kg=400, velocity="B")
            for sec in range(1, 4)
            for lvl in range(1, 5)
            for b in ["A", "B"]
        ],

        # ── Aisle 02 — PICKING (velocity A — near shipping) ──────────────────
        *[
            make_loc(f"02-{pos:02d}-01-A", "02", f"{pos:02d}", "01", "A",
                     ZoneType.PICKING, StorageType.DRY,
                     max_units=50, max_kg=100, velocity="A", w=60, h=50, d=40)
            for pos in range(1, 7)
        ],
    ]

    for loc in locations_to_seed:
        # Idempotent check
        existing = await db.execute(
            select(InventoryLocation.id).where(
                and_(
                    InventoryLocation.company_id == company_id,
                    InventoryLocation.warehouse_id == warehouse_id,
                    InventoryLocation.code == loc.code
                )
            )
        )
        if existing.scalar() is None:
            db.add(loc)
            created_count += 1

    await db.commit()

    return ApiResponse(
        status="success",
        data={"created": created_count, "skipped": len(locations_to_seed) - created_count},
        message=f"Seeded {created_count} locations (skipped {len(locations_to_seed) - created_count} existing)."
    )
