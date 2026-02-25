import enum
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column

from common.models import Base, MultiTenantBase

class ConceptType(str, enum.Enum):
    """
    Mirror of Interno.Inventory.Models.ConceptType.
    Defines the direction of inventory movement.
    """
    ENTRY = "Entry"      # Increases stock (Purchases, Returns from customers)
    OUTPUT = "Output"    # Decreases stock (Sales, Returns to suppliers)
    ADJUSTMENT = "Adjustment"  # Can increase or decrease (Cycle counts, corrections)
    TRANSFER = "Transfer"      # Multi-tenant or Inter-warehouse movement

class Concept(MultiTenantBase, Base):
    """
    Mirror of Interno.Inventory.Models.Concept.
    Master catalog of operation types (Compra, Venta, Ajuste, Transferencia).
    
    Defines:
    - The nature of the operation (Entry/Output/Adjustment)
    - Whether it affects physical stock
    - The code used for folio generation (e.g., 'ENT' for Entrada)
    """
    __tablename__ = "concepts"

    code: Mapped[str] = mapped_column(
        String(10), 
        nullable=False, 
        index=True,
        comment="Short code for folio generation (e.g., 'ENT', 'SAL', 'AJU')"
    )
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Display name (e.g., 'Entrada de Compra', 'Salida por Venta')"
    )
    description: Mapped[str] = mapped_column(
        String(250), 
        nullable=True,
        comment="Detailed description of when to use this concept"
    )
    
    concept_type: Mapped[ConceptType] = mapped_column(
        Enum(ConceptType),
        nullable=False,
        index=True,
        comment="Direction of movement: Entry, Output, or Adjustment"
    )
    
    affect_stock: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        nullable=False,
        comment="If True, movements with this concept will update InventorySnapshot"
    )

    __table_args__ = (
        # 🔒 Unique constraint: Each company has unique concept codes
        Index("ix_concept_tenant_code", "company_id", "code", unique=True),
    )

    def __repr__(self):
        return f"<Concept(code='{self.code}', name='{self.name}', type={self.concept_type})>"
