from decimal import Decimal
from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, composite
from common.domain.value_objects import Money
from common.models import BaseMovementConcept

class MovementConcept(BaseMovementConcept):
    """
    Categorization for Inventory Movements (Reasons).
    Example: 'Scrap', 'Cycle Count Adjustment', 'Production Consumption'.
    """
    __tablename__ = "inventory_movement_concepts"

    affects_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Financial Metadata (Optional Standard Price for this concept)
    _unit_price: Mapped[Decimal] = mapped_column("unit_price", Numeric(18, 4), nullable=True, default=0)
    _currency: Mapped[str] = mapped_column("currency", String(3), nullable=False, default="MXN")
    
    standard_price: Mapped[Money] = composite(Money, _unit_price, _currency)

    def __repr__(self):
        return f"<MovementConcept(name='{self.name}', type={self.type})>"
