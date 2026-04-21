import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, UniqueConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class UOM(MultiTenantBase):
    __tablename__ = 'uoms'

    # Override company_id to be nullable for Global records
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    abbreviation: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    plural: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    conversion_factor: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 8), nullable=True, default=1.0)
    translation_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    __table_args__ = (
        UniqueConstraint('code', 'company_id', name='uq_uom_code_company'),
    )

    # Enable Standard Optimistic Locking
