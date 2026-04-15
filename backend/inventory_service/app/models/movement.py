import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import Numeric, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, composite
from common.models import MultiTenantBase
from common.domain.value_objects import Money

class Movement(MultiTenantBase):
    """
    Immutable Ledger of inventory movements.
    """
    __tablename__ = "inventory_movements"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    
    # Movement data
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    
    # Financial Data via Money Value Object
    _amount: Mapped[Decimal] = mapped_column("unit_price", Numeric(18, 4), nullable=True, default=0)
    _currency: Mapped[str] = mapped_column("currency", String(3), nullable=False, default="MXN")
    
    price: Mapped[Money] = composite(Money, _amount, _currency)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False) # IN, OUT, ADJUSTMENT
    
    # Anexo 24 FIFO Compliance
    available_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0, nullable=False)
    customs_pedimento_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, index=True, nullable=True)
    source_movement_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, index=True, nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Categorization
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Traceability
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    
    comments: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Inherits created_at, created_by, and company_id from MultiTenantBase

    def __repr__(self):
        return f"<Movement(id={self.id}, type={self.movement_type}, qty={self.quantity})>"
