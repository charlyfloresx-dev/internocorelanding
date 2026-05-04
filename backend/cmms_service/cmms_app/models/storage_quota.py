"""StorageQuota — Control de capacidad de almacenamiento por tenant."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, Numeric, DateTime, Enum as SAEnum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase
from cmms_app.core.constants import StorageTier, QuotaApprovalStatus


class StorageQuota(MultiTenantBase):
    """
    Registro ÚNICO por company_id que trackea el consumo de almacenamiento.
    El BillingWorker actualiza bytes_used diariamente para el reporte mensual.
    El flag excess_approval_status controla si la empresa puede subir
    más archivos una vez superado el límite del tier.
    """
    __tablename__ = "cmms_storage_quotas"

    # ── Tier y límites ────────────────────────────────────────────────────────
    tier: Mapped[StorageTier] = mapped_column(SAEnum(StorageTier), default=StorageTier.BASIC, nullable=False)
    max_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    bytes_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ── Precio por excedente (dinámico por tier/negociación) ─────────────────
    price_per_excess_gb: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)

    # ── Aprobación de excedente (flujo Admin) ─────────────────────────────────
    excess_approval_status: Mapped[Optional[QuotaApprovalStatus]] = mapped_column(
        SAEnum(QuotaApprovalStatus), nullable=True
    )
    excess_approved_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excess_approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    excess_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Política de retención configurada por el tenant ───────────────────────
    evidence_retention_months: Mapped[int] = mapped_column(Integer, default=24, nullable=False)

    __table_args__ = (
        Index("ix_cmms_quota_company", "company_id", unique=True),
    )

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def effective_max_bytes(self) -> int:
        """Límite real = contratado + excedente aprobado."""
        extra = (
            self.excess_approved_bytes
            if self.excess_approval_status == QuotaApprovalStatus.APPROVED
            else 0
        )
        return self.max_bytes + extra

    @property
    def usage_pct(self) -> float:
        if self.effective_max_bytes == 0:
            return 0.0
        return round((self.bytes_used / self.effective_max_bytes) * 100, 2)

    @property
    def is_over_limit(self) -> bool:
        return self.bytes_used > self.effective_max_bytes
