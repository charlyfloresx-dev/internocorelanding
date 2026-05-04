"""
Pydantic Schemas — Storage Quota & Billing
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from cmms_app.core.constants import StorageTier, QuotaApprovalStatus


class StorageQuotaResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    tier: StorageTier
    max_bytes: int
    bytes_used: int
    usage_pct: float
    is_over_limit: bool
    price_per_excess_gb: Optional[Decimal] = None
    excess_approval_status: Optional[QuotaApprovalStatus] = None
    excess_approved_bytes: int
    evidence_retention_months: int
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExcessApprovalRequest(BaseModel):
    """Admin approves a storage overage for a specific amount of extra bytes."""
    approved_extra_bytes: int
    notes: Optional[str] = None


class BillingReportResponse(BaseModel):
    """Monthly billing summary shown to admin before approving excess charges."""
    company_id: uuid.UUID
    tier: StorageTier
    bytes_used: int
    max_bytes: int
    excess_bytes: int
    excess_gb: float
    price_per_excess_gb: Optional[Decimal] = None
    estimated_excess_charge: Optional[Decimal] = None
    currency: str = "USD"
    report_month: str  # e.g. "2026-05"
    generated_at: datetime
