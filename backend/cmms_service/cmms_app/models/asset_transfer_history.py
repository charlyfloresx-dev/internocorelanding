"""AssetTransferHistory — Historial de custodia / transferencia temporal entre bodegas."""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Text, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import MultiTenantBase
from cmms_app.core.constants import TransferType

if TYPE_CHECKING:
    from .asset import Asset


class AssetTransferHistory(MultiTenantBase):
    """
    Registro inmutable de cada movimiento de un activo entre bodegas.
    Soporta transferencias temporales (se espera fecha de retorno)
    y permanentes (cambio definitivo de custodia).
    """
    __tablename__ = "cmms_asset_transfers"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    transfer_type: Mapped[TransferType] = mapped_column(
        SAEnum(TransferType), default=TransferType.TEMPORARY, nullable=False
    )
    expected_return_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_return_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authorized_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="transfer_history")

    __table_args__ = (
        Index("ix_cmms_transfers_company_asset", "company_id", "asset_id"),
    )
