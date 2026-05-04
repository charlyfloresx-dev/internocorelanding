"""Storage Router — Quota management, evidence upload, billing report."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.infrastructure.database import get_db
from common.dependencies import get_current_company_id
from common.responses import success_response
from cmms_app.models import StorageQuota, MaintenanceEvidence, WorkOrder
from cmms_app.schemas import (
    StorageQuotaResponse, ExcessApprovalRequest, BillingReportResponse,
)
from cmms_app.core.constants import QuotaApprovalStatus
from cmms_app.services.storage_service import StorageService, QuotaExceededError

router = APIRouter(tags=["Storage & Billing"])
storage = StorageService()

# Max single file size: 50 MB
MAX_FILE_BYTES = 50 * 1024 * 1024


# ── GET /storage/quota ────────────────────────────────────────────────────────
@router.get("/quota")
async def get_quota(
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """Returns current storage usage and tier info for the company."""
    quota = await _get_or_create_quota(db, company_id)
    return success_response(data=StorageQuotaResponse.model_validate(quota).model_dump())


# ── POST /storage/evidence/{work_order_id} ────────────────────────────────────
@router.post("/evidence/{work_order_id}", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    work_order_id: uuid.UUID,
    file: UploadFile = File(...),
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """
    Evidence upload with pre-flight quota validation.
    - Validates WorkOrder belongs to company.
    - Validates file size <= 50 MB.
    - Runs quota check BEFORE storing (raises 402 if exceeded without approval).
    - Stores file and records MaintenanceEvidence with file_size_bytes.
    - Atomically updates StorageQuota.bytes_used.
    """
    # Validate WorkOrder ownership
    wo_result = await db.execute(
        select(WorkOrder).where(WorkOrder.id == work_order_id, WorkOrder.company_id == company_id)
    )
    if not wo_result.scalar_one_or_none():
        raise HTTPException(404, "Work order not found.")

    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > MAX_FILE_BYTES:
        raise HTTPException(413, f"File too large. Maximum size is {MAX_FILE_BYTES // (1024*1024)} MB.")

    # Pre-flight quota check
    try:
        quota = await storage.validate_quota(db, company_id, file_size)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "QUOTA_EXCEEDED",
                "bytes_used": e.used,
                "bytes_limit": e.limit,
                "pending_approval": e.pending_approval,
                "message": "Storage quota exceeded. Admin approval required to continue uploading.",
            },
        )

    # Upload to S3 or local
    filename = f"{work_order_id}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}"
    path = await storage.upload(company_id, file_bytes, filename, sub_path="maintenance")

    # Persist evidence record
    evidence = MaintenanceEvidence(
        work_order_id=work_order_id,
        file_name=file.filename or filename,
        file_path=path,
        file_size_bytes=file_size,
        mime_type=file.content_type or "application/octet-stream",
        description=description,
        captured_at=datetime.now(timezone.utc),
        company_id=company_id,
        tenant_id=company_id,
    )
    db.add(evidence)

    # Update quota counter atomically
    await storage.deduct_quota(db, quota, file_size)

    await db.commit()
    await db.refresh(evidence)

    return success_response(
        data={"evidence_id": str(evidence.id), "file_path": path, "file_size_bytes": file_size},
        message="Evidence uploaded successfully.",
    )


# ── GET /storage/evidence/{work_order_id}/{evidence_id}/url ──────────────────
@router.get("/evidence/{work_order_id}/{evidence_id}/url")
async def get_evidence_url(
    work_order_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """Returns a pre-signed URL (S3) or local path for direct browser access."""
    result = await db.execute(
        select(MaintenanceEvidence).where(
            MaintenanceEvidence.id == evidence_id,
            MaintenanceEvidence.work_order_id == work_order_id,
            MaintenanceEvidence.company_id == company_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(404, "Evidence not found.")

    url = storage.generate_presigned_url(evidence.file_path)
    return success_response(data={"url": url, "expires_in_seconds": 3600})


# ── POST /storage/quota/approve-excess ───────────────────────────────────────
@router.post("/quota/approve-excess")
async def approve_excess(
    payload: ExcessApprovalRequest,
    approver_id: uuid.UUID,  # Injected from JWT in production (simplified here)
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """
    Admin approves additional storage capacity.
    Sets excess_approval_status=APPROVED and increments excess_approved_bytes.
    """
    quota = await _get_or_create_quota(db, company_id)
    quota.excess_approved_bytes += payload.approved_extra_bytes
    quota.excess_approval_status = QuotaApprovalStatus.APPROVED
    quota.excess_approved_by_id = approver_id
    quota.excess_approved_at = datetime.now(timezone.utc)
    db.add(quota)
    await db.commit()
    await db.refresh(quota)
    return success_response(
        data=StorageQuotaResponse.model_validate(quota).model_dump(),
        message=f"Approved {payload.approved_extra_bytes / (1024**3):.2f} GB extra capacity.",
    )


# ── GET /storage/billing-report ───────────────────────────────────────────────
@router.get("/billing-report")
async def get_billing_report(
    db: AsyncSession = Depends(get_db),
    company_id: uuid.UUID = Depends(get_current_company_id),
):
    """Monthly billing summary shown to Admin before approving excess charges."""
    quota = await _get_or_create_quota(db, company_id)
    now = datetime.now(timezone.utc)
    excess_bytes = max(0, quota.bytes_used - quota.max_bytes)
    excess_gb = excess_bytes / (1024 ** 3)

    estimated_charge = None
    if quota.price_per_excess_gb and excess_gb > 0:
        estimated_charge = quota.price_per_excess_gb * round(excess_gb, 4)

    report = BillingReportResponse(
        company_id=company_id,
        tier=quota.tier,
        bytes_used=quota.bytes_used,
        max_bytes=quota.max_bytes,
        excess_bytes=excess_bytes,
        excess_gb=round(excess_gb, 4),
        price_per_excess_gb=quota.price_per_excess_gb,
        estimated_excess_charge=estimated_charge,
        currency="USD",
        report_month=now.strftime("%Y-%m"),
        generated_at=now,
    )
    return success_response(data=report.model_dump())


# ── Helper ────────────────────────────────────────────────────────────────────
async def _get_or_create_quota(db: AsyncSession, company_id: uuid.UUID) -> StorageQuota:
    from cmms_app.core.config import settings
    result = await db.execute(
        select(StorageQuota).where(StorageQuota.company_id == company_id)
    )
    quota = result.scalar_one_or_none()
    if not quota:
        quota = StorageQuota(
            company_id=company_id,
            tenant_id=company_id,
            max_bytes=settings.TIER_BASIC_BYTES,
            bytes_used=0,
        )
        db.add(quota)
        await db.flush()
    return quota
