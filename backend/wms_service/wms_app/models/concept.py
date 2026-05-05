import enum
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column

from common.models import Base, MultiTenantBase

from common.models import BaseMovementConcept, IdempotencyKey
from common.enums import MovementType

# Alias de compatibilidad: handlers.py usa ConceptType
ConceptType = MovementType

class Concept(BaseMovementConcept):
    """
    Mirror of Interno.Inventory.Models.Concept.
    Master catalog of operation types (Compra, Venta, Ajuste, Transferencia).
    """
    __tablename__ = "concepts"

    affect_stock: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        nullable=False,
        comment="If True, movements with this concept will update InventorySnapshot"
    )

    # RE-MAPEO DE COLUMNA PARA COMPATIBILIDAD CON MIGRACIÓN BASE (concept_type)
    type: Mapped[MovementType] = mapped_column(
        "concept_type",
        Enum(MovementType),
        nullable=False
    )

    __table_args__ = (
        # 🔒 Unique constraint: Each company has unique concept codes
        Index("ix_concept_tenant_code", "company_id", "code", unique=True),
    )

    def __repr__(self):
        return f"<Concept(code='{self.code}', name='{self.name}', type={self.type})>"
