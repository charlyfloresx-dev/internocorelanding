import enum
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Numeric, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Importamos las bases según arquitectura [2026-01-20]
from common.models import Base, MultiTenantBase

if TYPE_CHECKING:
    from .inventory_document import InventoryDocument
    from .warehouse import Warehouse
    from .product import Product

class InventoryMovement(MultiTenantBase, Base):
    """
    Líneas de detalle del documento de inventario (Ledger Lines).
    Registra el movimiento físico y financiero de cada SKU.
    """
    __tablename__ = "inventory_movements"

    # --- 🔑 TRIPLE IDENTITY (Line Level) ---
    # 1. id (UUID): Heredado de Base
    # 2. sequence_number: Número de línea (1, 2, 3...) dentro del documento
    sequence_number: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="Número secuencial de línea dentro del documento"
    )

    # --- 🔗 RELACIONES ---
    document_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("inventory_documents.id"), 
        index=True,
        nullable=False
    )
    
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("products.id"), 
        index=True,
        nullable=False
    )

    warehouse_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warehouses.id"),
        index=True,
        nullable=False
    )

    # --- 📦 LOGÍSTICA ---
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), 
        nullable=False,
        comment="Cantidad movida (soporta hasta 4 decimales)"
    )
    
    lot_number: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True, 
        index=True
    )
    
    affected_stock: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Indica si este movimiento debe impactar el stock actual"
    )

    # --- 💰 FINANZAS (Instrucción 2026-02-09) ---
    # Precios indicados basados en compañía y almacén
    purchase_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), 
        default=0,
        comment="Costo unitario de compra al momento del movimiento"
    )
    sell_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), 
        default=0,
        comment="Precio unitario de venta"
    )
    total_line: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), 
        default=0,
        comment="Total de la línea (quantity * price)"
    )

    # --- 📑 AUDITORÍA / LEDGER ---
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(36), 
        index=True,
        comment="ID de transacción para trazabilidad cruzada"
    )

    # --- 🧩 ORM RELATIONSHIPS ---
    document: Mapped["InventoryDocument"] = relationship(
        "InventoryDocument", 
        back_populates="movements"
    )
    
    product: Mapped["Product"] = relationship("Product")

    # --- 🔒 CONSTRAINTS ---
    __table_args__ = (
        # Unicidad: No pueden haber dos líneas con el mismo número en un documento
        Index("ix_mov_doc_sequence", "document_id", "sequence_number", unique=True),
    )