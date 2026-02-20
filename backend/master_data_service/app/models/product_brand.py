from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from common.domain.entities import MultiTenantBase

class ProductBrand(MultiTenantBase):
    __tablename__ = 'product_brands'

    # Nullable company_id for Global Brands
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    translation_key = Column(String(100), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint('code', 'company_id', name='uq_brand_code_company'),
    )