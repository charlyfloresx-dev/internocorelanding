import uuid
import enum
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Numeric, Enum, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase

class TransactionType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    BACKFLUSHING = "BACKFLUSHING"

class InventoryLevel(MultiTenantBase):
    __tablename__ = "inventory_levels"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=Decimal("0.0"))
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=Decimal("0.0"))
    
    # --- VALORACIÓN (WMS/CORE) ---
    weighted_average_cost: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=Decimal("0.0"))
    last_purchase_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=Decimal("0.0"))
    replacement_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=Decimal("0.0"))
    
    currency_code: Mapped[str] = mapped_column(String(3), server_default="USD", default="USD")

    __table_args__ = (
        UniqueConstraint("company_id", "warehouse_id", "product_id", name="uq_inventory_level_per_company"),
    )

class InventoryTransaction(MultiTenantBase):
    __tablename__ = "inventory_transactions"
    
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    previous_balance: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    new_balance: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    
    reference_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=True) 
    comments: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
