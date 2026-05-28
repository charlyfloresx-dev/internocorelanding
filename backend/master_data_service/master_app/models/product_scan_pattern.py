import uuid
from sqlalchemy import String, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase


class ProductScanPattern(MultiTenantBase):
    """
    Per-item scan validation rules. Each active pattern is a regex the scan input
    must satisfy. Used by both MES ScannerService and Flutter POS ScannerBloc.
    SSOT in master_data_service — fetched at scan time (embedded in lookup response).
    """
    __tablename__ = "master_product_scan_patterns"

    item_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pattern_name: Mapped[str] = mapped_column(String(100), nullable=False)
    regex: Mapped[str] = mapped_column(String(500), nullable=False)
    error_message: Mapped[str] = mapped_column(String(500), nullable=False)
    # is_active inherited from BaseDomainEntity (True = active pattern, False = soft-deleted)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "item_code", "pattern_name",
                         name="uq_scan_pattern_company_item_name"),
        Index("ix_scan_patterns_company_item_active",
              "company_id", "item_code", "is_active"),
    )
