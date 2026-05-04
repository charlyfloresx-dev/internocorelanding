"""Asset — Activo industrial con jerarquía padre-hijo y QR HMAC."""
import uuid
import hmac
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .maintenance_plan import MaintenancePlan
    from .work_order import MaintenanceWorkOrder
    from .asset_transfer_history import AssetTransferHistory

from sqlalchemy import String, Text, Integer, Numeric, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import MultiTenantBase
from cmms_app.core.constants import AssetCategory, AssetCriticality, AssetStatus


class Asset(MultiTenantBase):
    __tablename__ = "cmms_assets"

    # ── Identificación ──────────────────────────────────────────────────────
    internal_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(150), unique=True, nullable=True)

    # ── Clasificación ───────────────────────────────────────────────────────
    category: Mapped[AssetCategory] = mapped_column(SAEnum(AssetCategory), default=AssetCategory.MACHINERY, nullable=False, index=True)
    criticality: Mapped[AssetCriticality] = mapped_column(SAEnum(AssetCriticality), default=AssetCriticality.MEDIUM, nullable=False, index=True)
    status: Mapped[AssetStatus] = mapped_column(SAEnum(AssetStatus), default=AssetStatus.OPERATIONAL, nullable=False, index=True)

    # ── Ubicación (weak-ref al inventario) ──────────────────────────────────
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    location_notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Jerarquía ───────────────────────────────────────────────────────────
    parent_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── Fechas técnicas ─────────────────────────────────────────────────────
    purchase_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    installation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    warranty_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Responsable (weak-ref a colaborators) ───────────────────────────────
    responsible_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # ── Especificaciones dinámicas ───────────────────────────────────────────
    specifications: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # ── Métricas MTBF/MTTR (calculadas, cacheadas) ──────────────────────────
    mtbf_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    mttr_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0–100

    # ── QR Identity (HMAC-signed) ────────────────────────────────────────────
    qr_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # ── Relationships ────────────────────────────────────────────────────────
    children: Mapped[List["Asset"]] = relationship("Asset", back_populates="parent", foreign_keys=[parent_asset_id], cascade="all")
    parent: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="children", remote_side="Asset.id", foreign_keys=[parent_asset_id])
    maintenance_plans: Mapped[List["MaintenancePlan"]] = relationship("MaintenancePlan", back_populates="asset", cascade="all, delete-orphan")
    work_orders: Mapped[List["MaintenanceWorkOrder"]] = relationship("MaintenanceWorkOrder", back_populates="asset", cascade="all, delete-orphan")
    transfer_history: Mapped[List["AssetTransferHistory"]] = relationship("AssetTransferHistory", back_populates="asset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cmms_assets_company_status", "company_id", "status"),
        Index("ix_cmms_assets_company_warehouse", "company_id", "warehouse_id"),
        Index("ix_cmms_assets_company_code", "company_id", "internal_code", unique=True),
    )

    def generate_qr_token(self, secret: str) -> str:
        payload = f"v1/assets/{self.id}"
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        self.qr_token = sig
        return f"{payload}?sig={sig}"
