import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Solo importamos el nivel más alto de la jerarquía
from common.models import Base, MultiTenantBase 

if TYPE_CHECKING:
    from .warehouse import Warehouse
    from .inventory_movement import InventoryMovement
    from .concept import Concept

class DocumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

# Al heredar de MultiTenantBase, ya tienes ID, CreatedAt, UpdatedAt y CompanyId
class InventoryDocument(MultiTenantBase):
    __tablename__ = "inventory_documents"
    
    # ... (el resto igual)

    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    folio: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), 
        default=DocumentStatus.DRAFT,
        nullable=False
    )
    
    observations: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- 🔗 RELACIONES ---
    warehouse_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id"), index=True)
    concept_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("concepts.id"), index=True)

    # --- 🌍 INTER-COMPANY ---
    target_company_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    target_warehouse_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # --- 💰 FINANZAS ---
    sub_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))
    total: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"))

    # Relaciones ORM
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="documents")
    concept: Mapped["Concept"] = relationship("Concept")
    
    movements: Mapped[List["InventoryMovement"]] = relationship(
        "InventoryMovement", 
        back_populates="document", 
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        # 🔒 Unique constraint: El número de secuencia debe ser único por compañía
        UniqueConstraint('company_id', 'sequence_number', name='uq_document_company_sequence'),
    )