from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import Optional
from common.models import MultiTenantBase

class ProductBrand(MultiTenantBase):
    __tablename__ = 'product_brands'

    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    translation_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint('code', 'company_id', name='uq_brand_code_company'),
    )
    
    # Enable Standard Optimistic Locking
