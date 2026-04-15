import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class StockLot(MultiTenantBase):
    """
    Squeleto de la tabla stock_lots para trazabilidad por lote y fecha de vencimiento.
    """
    __tablename__ = "stock_lots"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    expiration_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<StockLot(product_id={self.product_id}, batch={self.batch_number}, qty={self.quantity})>"
