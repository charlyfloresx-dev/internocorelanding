"""
StorageService — Pre-flight quota validator + provider abstraction.
Validates capacity BEFORE any file upload reaches S3 or local FS.
"""
import os
import hmac
import hashlib
import uuid
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from cmms_app.core.config import settings
from cmms_app.models import StorageQuota
from cmms_app.core.constants import QuotaApprovalStatus


class QuotaExceededError(Exception):
    """Raised when an upload would exceed the company's approved storage limit."""
    def __init__(self, used: int, limit: int, pending_approval: bool = False):
        self.used = used
        self.limit = limit
        self.pending_approval = pending_approval
        super().__init__(
            f"Storage quota exceeded: {used} / {limit} bytes. "
            f"{'Pending admin approval.' if pending_approval else 'No excess approved.'}"
        )


class StorageService:
    """
    Abstraction layer for S3 and LocalFileSystem.
    Controlled by STORAGE_TYPE env variable: 's3' | 'local'.

    Usage:
        storage = StorageService()
        await storage.validate_quota(db, company_id, file_size_bytes)
        path = await storage.upload(company_id, file_bytes, filename)
    """

    def __init__(self):
        self._type = settings.STORAGE_TYPE

        if self._type == "s3":
            self._s3 = boto3.client("s3", region_name=settings.S3_REGION)
            self._bucket = settings.S3_BUCKET_NAME
        else:
            self._local_root = Path(settings.LOCAL_STORAGE_PATH)
            self._local_root.mkdir(parents=True, exist_ok=True)

    # ── Quota validation (pre-flight) ─────────────────────────────────────────

    async def validate_quota(
        self,
        db: AsyncSession,
        company_id: uuid.UUID,
        new_file_bytes: int,
    ) -> StorageQuota:
        """
        Raises QuotaExceededError if the upload would exceed the approved limit.
        Returns the StorageQuota record for downstream use.
        """
        result = await db.execute(
            select(StorageQuota).where(StorageQuota.company_id == company_id)
        )
        quota: Optional[StorageQuota] = result.scalar_one_or_none()

        if quota is None:
            # Auto-provision Basic tier for new companies
            quota = StorageQuota(
                company_id=company_id,
                tenant_id=company_id,
                max_bytes=settings.TIER_BASIC_BYTES,
                bytes_used=0,
            )
            db.add(quota)
            await db.flush()

        projected = quota.bytes_used + new_file_bytes

        if projected > quota.effective_max_bytes:
            pending = (
                quota.excess_approval_status == QuotaApprovalStatus.PENDING
            )
            raise QuotaExceededError(
                used=quota.bytes_used,
                limit=quota.effective_max_bytes,
                pending_approval=pending,
            )

        return quota

    async def deduct_quota(
        self,
        db: AsyncSession,
        quota: StorageQuota,
        file_size_bytes: int,
    ) -> None:
        """Increment bytes_used after a successful upload."""
        quota.bytes_used += file_size_bytes
        db.add(quota)

    async def release_quota(
        self,
        db: AsyncSession,
        company_id: uuid.UUID,
        file_size_bytes: int,
    ) -> None:
        """Decrement bytes_used after a file deletion (retention cleanup)."""
        result = await db.execute(
            select(StorageQuota).where(StorageQuota.company_id == company_id)
        )
        quota: Optional[StorageQuota] = result.scalar_one_or_none()
        if quota and quota.bytes_used >= file_size_bytes:
            quota.bytes_used -= file_size_bytes
            db.add(quota)

    # ── Upload ────────────────────────────────────────────────────────────────

    async def upload(
        self,
        company_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        sub_path: str = "evidence",
    ) -> str:
        """
        Stores the file and returns the storage key/path.
        Path format: {company_id}/{sub_path}/{filename}
        """
        key = f"{company_id}/{sub_path}/{filename}"

        if self._type == "s3":
            self._s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=file_bytes,
            )
        else:
            dest = self._local_root / str(company_id) / sub_path
            dest.mkdir(parents=True, exist_ok=True)
            (dest / filename).write_bytes(file_bytes)

        return key

    # ── Pre-signed URL ────────────────────────────────────────────────────────

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Returns a time-limited URL for direct browser download.
        Only available in S3 mode; local mode returns a local path stub.
        """
        if self._type == "s3":
            return self._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        return f"/static/{key}"

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(self, key: str) -> None:
        if self._type == "s3":
            self._s3.delete_object(Bucket=self._bucket, Key=key)
        else:
            target = self._local_root / key
            if target.exists():
                target.unlink()


# ── QR Token Helpers ──────────────────────────────────────────────────────────

def generate_qr_payload(entity_type: str, entity_id: uuid.UUID) -> tuple[str, str]:
    """
    Generates a signed QR payload.
    Returns (full_url_string, short_sig) using HMAC-SHA256.
    Format: v1/{entity_type}/{entity_id}?sig={16-char-hex}
    """
    secret = settings.QR_SIGNING_SECRET
    payload = f"v1/{entity_type}/{entity_id}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{payload}?sig={sig}", sig


def verify_qr_signature(entity_type: str, entity_id: str, sig: str) -> bool:
    """Validates that a QR code's signature matches the system secret."""
    secret = settings.QR_SIGNING_SECRET
    payload = f"v1/{entity_type}/{entity_id}"
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return hmac.compare_digest(expected, sig)
