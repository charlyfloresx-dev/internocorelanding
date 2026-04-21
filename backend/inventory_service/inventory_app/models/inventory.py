import uuid
import enum
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, Numeric, Enum, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, composite
from sqlalchemy.dialects.postgresql import UUID

from common.models import MultiTenantBase
from common.domain.value_objects import Money

from inventory_app.domain.entities.inventory_item import TransactionType

class InventoryLevel(MultiTenantBase):
    __tablename__ = "inventory_levels"

    warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True, nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=Decimal("0.0"))
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), server_default="0", default=Decimal("0.0"))
    
    # --- VALORACIÓN (WMS/CORE) ---
    _wac_amount: Mapped[Decimal] = mapped_column("wac_amount", Numeric(18, 4), server_default="0", default=Decimal("0.0"))
    _wac_currency: Mapped[str] = mapped_column("wac_currency", String(3), server_default="USD", default="USD")
    wac: Mapped[Money] = composite(Money, _wac_amount, _wac_currency)

    _last_amount: Mapped[Decimal] = mapped_column("last_price_amount", Numeric(18, 4), server_default="0", default=Decimal("0.0"))
    _last_currency: Mapped[str] = mapped_column("last_price_currency", String(3), server_default="USD", default="USD")
    last_price: Mapped[Money] = composite(Money, _last_amount, _last_currency)

    _repl_amount: Mapped[Decimal] = mapped_column("replacement_price_amount", Numeric(18, 4), server_default="0", default=Decimal("0.0"))
    _repl_currency: Mapped[str] = mapped_column("replacement_price_currency", String(3), server_default="USD", default="USD")
    replacement_price: Mapped[Money] = composite(Money, _repl_amount, _repl_currency)

    @property
    def available_quantity(self) -> Decimal:
        """SSOT Calculation: Available = Total - Reserved"""
        return self.quantity - self.reserved_quantity

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
