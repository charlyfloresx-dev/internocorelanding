"""
ORM Models para Refresh Token Rotation Stateless.

Implementa:
- RefreshTokenFamily: Familia de tokens con seguimiento de generación
- RefreshTokenRotationAudit: Append-only audit log para forensics
"""
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, DateTime, UUID as SQL_UUID, Boolean, Text, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from common.infrastructure.models.base import MultiTenantBase


class RefreshTokenFamily(MultiTenantBase):
    """
    Familia de tokens stateless con seguimiento de generación y revocación.

    Hereda de MultiTenantBase:
    - id: UUID PK
    - company_id: UUID FK → companies.id
    - created_at, updated_at, created_by, updated_by, deleted_at
    - is_active: bool (soft delete)
    - version_id: int (optimistic locking built-in)

    PATRÓN:
    - Cada refresh creaSXXXXa nueva generación (0 → 1 → 2 ...)
    - Reuse detectado (gap en generación) → family revocada
    - Failover resilience: 2-second idempotency window
    """
    __tablename__ = "refresh_token_families"

    # PK (heredado de MultiTenantBase)
    id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    # Foreign Keys (multi-tenancy)
    company_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Cryptographic Sealing
    family_salt: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True
    )
    # 32 bytes = 64 hex chars. Unique para prevenir colisiones.

    # Generation Tracking (Optimistic Locking)
    current_generation: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )
    # Incrementa: 0 → 1 → 2 ... con cada refresh exitoso

    version_counter: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )
    # Usado para optimistic locking: prevenir race conditions

    # Revocation State
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    # NULL = activa. NOT NULL = revocada (breach o logout)

    revocation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    # 'REUSE_DETECTED' | 'USER_LOGOUT' | 'SECURITY_ALERT' | ...

    # Failover Resilience (RDS Failover)
    last_refresh_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default="now()"
    )
    # Timestamp del último refresh exitoso

    last_refresh_jti: Mapped[UUID | None] = mapped_column(
        SQL_UUID(as_uuid=True),
        nullable=True
    )
    # JTI del último refresh token emitido (para idempotencia)

    refresh_window_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    # Ventana de 2 segundos para detectar retries idempotentes post-failover

    # Timestamps y auditoría (heredados de MultiTenantBase)
    # created_at, updated_at, created_by, updated_by, deleted_at

    # Índices para queries críticas
    __table_args__ = (
        Index("idx_user_company_family", "user_id", "company_id"),
        Index("idx_revoked_families", "revoked_at"),
        Index("idx_refresh_window", "refresh_window_expires_at"),
    )

    def is_active(self) -> bool:
        """True si NO está revocada."""
        return self.revoked_at is None


class RefreshTokenRotationAudit(MultiTenantBase):
    """
    Append-only audit log para forensics de breach y análisis de race conditions.

    INVARIANTE: NUNCA se actualiza ni borra—solo se inserta.
    Permite investigar:
    - Timelines de breach
    - Patrones de reuse
    - Race conditions (concurrent_attempt_detected)
    - Failover scenarios (failover_detected)
    """
    __tablename__ = "refresh_token_rotation_audit"

    id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )

    # Foreign Key
    family_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("refresh_token_families.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Tenant context (denormalized para queries rápidas)
    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    company_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # Action log
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )
    # Valores: 'CREATED' | 'ROTATED' | 'REUSE_DETECTED' | 'REVOKED' | 'IDEMPOTENT_RETRY' | 'CONCURRENT_GRACEFUL'

    old_generation: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    new_generation: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    # Network context (para investigación de breach)
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Anomaly flags
    concurrent_attempt_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false"
    )
    failover_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false"
    )

    # Timestamps (heredados: created_at, updated_by)

    __table_args__ = (
        Index("idx_family_audit_timeline", "family_id", "created_at"),
        Index("idx_reuse_detection", "action", "created_at"),
    )
