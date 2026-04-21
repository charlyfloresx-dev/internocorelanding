import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from common.infrastructure.models.base import MultiTenantBase


class RefreshToken(MultiTenantBase):
    """
    Persists refresh tokens scoped to a specific tenant-company pair.

    Security Invariants:
    - Rotation: each use issues a new token and revokes the previous one.
    - Replay Attack Prevention: token_hash stores SHA-256(token) — never plaintext.
    - Zero-Trust Tenant Isolation: company_id and tenant_id enforced at the DB level.

    Inherits from MultiTenantBase → provides: id, company_id, tenant_id, group_id,
    created_at, updated_at, created_by, updated_by, deleted_at, transaction_id,
    is_active, version_id.
    """
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA-256 hex digest of the raw token string — never store plaintext.
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

