from sqlalchemy import Column, String, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from common.domain.entities import MultiTenantBase

class UOM(MultiTenantBase):
    __tablename__ = 'uoms'

    # Override company_id to be nullable for Global records
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    code = Column(String(10), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    plural = Column(String(50), nullable=True)
    translation_key = Column(String(100), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint('code', 'company_id', name='uq_uom_code_company'),
    )