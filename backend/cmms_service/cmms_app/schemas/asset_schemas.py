"""
Pydantic Schemas — Assets
Request/Response contracts for the Asset domain.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

from pydantic import BaseModel, Field

from cmms_app.core.constants import (
    AssetCategory, AssetCriticality, AssetStatus,
)


# ─────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────

class AssetBase(BaseModel):
    internal_code: str = Field(..., max_length=50, examples=["CNC-01"])
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=150)
    category: AssetCategory = AssetCategory.MACHINERY
    criticality: AssetCriticality = AssetCriticality.MEDIUM
    warehouse_id: uuid.UUID
    location_notes: Optional[str] = None
    parent_asset_id: Optional[uuid.UUID] = None
    purchase_date: Optional[datetime] = None
    installation_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    responsible_id: Optional[uuid.UUID] = None
    specifications: Optional[dict[str, Any]] = None


# ─────────────────────────────────────────────
# CREATE / UPDATE
# ─────────────────────────────────────────────

class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    category: Optional[AssetCategory] = None
    criticality: Optional[AssetCriticality] = None
    status: Optional[AssetStatus] = None
    warehouse_id: Optional[uuid.UUID] = None
    location_notes: Optional[str] = None
    responsible_id: Optional[uuid.UUID] = None
    specifications: Optional[dict[str, Any]] = None
    warranty_expiry: Optional[datetime] = None


# ─────────────────────────────────────────────
# RESPONSE
# ─────────────────────────────────────────────

class AssetResponse(AssetBase):
    id: uuid.UUID
    status: AssetStatus
    health_score: Optional[int] = None
    mtbf_hours: Optional[Decimal] = None
    mttr_hours: Optional[Decimal] = None
    qr_token: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AssetListResponse(BaseModel):
    """Lightweight card view for the industrial dashboard."""
    id: uuid.UUID
    internal_code: str
    name: str
    category: AssetCategory
    criticality: AssetCriticality
    status: AssetStatus
    warehouse_id: uuid.UUID
    health_score: Optional[int] = None
    next_maintenance: Optional[datetime] = None   # from active MaintenancePlan

    model_config = {"from_attributes": True}
