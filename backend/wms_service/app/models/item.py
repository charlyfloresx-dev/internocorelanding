import uuid
from sqlalchemy import String, Float, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from common.models import MultiTenantBase

class Item(MultiTenantBase):
    __tablename__ = "items"

    master_product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    stock_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    bin_location: Mapped[str] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint('sku', 'version_number', 'company_id', name='_wms_company_sku_version_uc'),
    )