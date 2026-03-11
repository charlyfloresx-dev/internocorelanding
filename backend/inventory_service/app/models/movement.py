import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from sqlalchemy import Numeric, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class Movement(MultiTenantBase):
    """
    Immutable Ledger of inventory movements.
    """
    __tablename__ = "inventory_movements"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    
    # Movement data
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False) # IN, OUT, ADJUSTMENT
    
    # Categorization
    concept_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=True)
    
    # Traceability
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    
    comments: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Inherits created_at, created_by, and company_id from MultiTenantBase

    def __repr__(self):
        return f"<Movement(id={self.id}, type={self.movement_type}, qty={self.quantity})>"
