"""Asset Router — CRUD + QR generation + transfer history."""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from common.infrastructure.database import get_db
from common.dependencies import get_current_company_id
from common.responses import success_response
from cmms_app.models import Asset, MaintenancePlan
from cmms_app.schemas import AssetCreate, AssetUpdate, AssetResponse, AssetListResponse
from cmms_app.core.config import settings
from cmms_app.services.storage_service import generate_qr_payload

router = APIRouter(tags=["Assets"])


# ── GET /assets ───────────────────────────────────────────────────────────────
@router.get("/")
async def list_assets(
    warehouse_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """Dashboard card list — filtered by company_id (multitenancy enforced)."""
    filters = [Asset.company_id == company_id, Asset.is_active == True]
    if warehouse_id:
        filters.append(Asset.warehouse_id == warehouse_id)
    if status:
        filters.append(Asset.status == status)

    result = await db.execute(select(Asset).where(and_(*filters)))
    assets = result.scalars().all()

    # Attach next_maintenance from active MaintenancePlan
    data = []
    for asset in assets:
        plan_result = await db.execute(
            select(MaintenancePlan.next_execution_date)
            .where(
                MaintenancePlan.asset_id == asset.id,
                MaintenancePlan.is_active == True,
                MaintenancePlan.company_id == company_id,
            )
            .order_by(MaintenancePlan.next_execution_date.asc())
            .limit(1)
        )
        next_maint = plan_result.scalar_one_or_none()
        row = AssetListResponse.model_validate(asset)
        row.next_maintenance = next_maint
        data.append(row)

    return success_response(data=[r.model_dump() for r in data])


# ── POST /assets ──────────────────────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    # Uniqueness check: internal_code per company
    existing = await db.execute(
        select(Asset).where(
            Asset.company_id == company_id,
            Asset.internal_code == payload.internal_code,
            Asset.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset with code '{payload.internal_code}' already exists in this company.",
        )

    asset = Asset(**payload.model_dump(), company_id=company_id, tenant_id=company_id)
    asset.generate_qr_token(settings.QR_SIGNING_SECRET)

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return success_response(
        data=AssetResponse.model_validate(asset).model_dump(),
        message="Asset created successfully.",
    )


# ── GET /assets/{asset_id} ────────────────────────────────────────────────────
@router.get("/{asset_id}")
async def get_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    asset = await _get_asset_or_404(db, asset_id, company_id)
    return success_response(data=AssetResponse.model_validate(asset).model_dump())


# ── PATCH /assets/{asset_id} ──────────────────────────────────────────────────
@router.patch("/{asset_id}")
async def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    asset = await _get_asset_or_404(db, asset_id, company_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return success_response(data=AssetResponse.model_validate(asset).model_dump())


# ── DELETE /assets/{asset_id} (soft-delete) ───────────────────────────────────
@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    asset = await _get_asset_or_404(db, asset_id, company_id)
    asset.is_active = False
    db.add(asset)
    await db.commit()


# ── GET /assets/{asset_id}/qr ─────────────────────────────────────────────────
@router.get("/{asset_id}/qr")
async def get_asset_qr(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """Returns the HMAC-signed QR payload for printing/scanning."""
    asset = await _get_asset_or_404(db, asset_id, company_id)
    qr_url, sig = generate_qr_payload("assets", asset.id)
    return success_response(data={"qr_url": qr_url, "sig": sig, "asset_id": str(asset.id)})


# ── Helper ────────────────────────────────────────────────────────────────────
async def _get_asset_or_404(db: AsyncSession, asset_id: uuid.UUID, company_id: uuid.UUID) -> Asset:
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.company_id == company_id, Asset.is_active == True)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")
    return asset
