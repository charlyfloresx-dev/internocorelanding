import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Numeric, Enum, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class BackflushErrorType(str, enum.Enum):
    MISSING_BOM = "MISSING_BOM"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    INVALID_PRODUCT = "INVALID_PRODUCT"

class BackflushStatus(str, enum.Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"
    FAILED_MANUAL_REVIEW = "FAILED_MANUAL_REVIEW"

class BackflushError(MultiTenantBase):
    """
    Tracks failed backflushing attempts for asynchronous resolution.
    This ensures manufacturing is never blocked by inventory data issues.
    """
    __tablename__ = "inventory_backflush_errors"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Context from MES
    event_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    production_run_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    
    # Problematic item
    item_code: Mapped[str] = mapped_column(String(100), nullable=False)
    required_qty: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    
    error_type: Mapped[BackflushErrorType] = mapped_column(Enum(BackflushErrorType), nullable=False)
    status: Mapped[BackflushStatus] = mapped_column(Enum(BackflushStatus), default=BackflushStatus.PENDING)
    
    # Reconciliation Tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_retry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    error_details: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<BackflushError(event={self.event_id}, item='{self.item_code}', type={self.error_type}, status={self.status})>"
