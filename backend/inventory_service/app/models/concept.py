import enum
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class ConceptType(str, enum.Enum):
    ENTRY = "ENTRY"
    OUTPUT = "OUTPUT"

class MovementConcept(MultiTenantBase):
    """
    Categorization for Inventory Movements (Reasons).
    Example: 'Scrap', 'Cycle Count Adjustment', 'Production Consumption'.
    """
    __tablename__ = "inventory_movement_concepts"

    # id is inherited from MultiTenantBase -> AuditBase -> BaseDomainEntity
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    type: Mapped[ConceptType] = mapped_column(String(20), nullable=False)
    affects_stock: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self):
        return f"<MovementConcept(name='{self.name}', type={self.type})>"
