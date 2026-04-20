import uuid
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase

class UOMConversion(MultiTenantBase):
    __tablename__ = 'uom_conversions'

    from_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("uoms.id"), nullable=False)
    to_uom_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("uoms.id"), nullable=False)
    factor: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)

    from_uom = relationship("UOM", foreign_keys=[from_uom_id])
    to_uom = relationship("UOM", foreign_keys=[to_uom_id])

    __table_args__ = (
        UniqueConstraint('from_uom_id', 'to_uom_id', 'company_id', name='uq_uom_conversion_src_dest_company'),
    )

    def __repr__(self) -> str:
        return f"<UOMConversion(from={self.from_uom_id}, to={self.to_uom_id}, factor={self.factor})>"
