import enum
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Numeric, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite

# Importamos las bases según arquitectura [2026-01-20]
from common.models import Base, MultiTenantBase
from common.domain.value_objects import Money

if TYPE_CHECKING:
    from .inventory_document import InventoryDocument
    from .warehouse import Warehouse
    from .item import Item

class InventoryMovement(MultiTenantBase):
    """
    Líneas de detalle del documento de inventario (Ledger Lines).
    Registra el movimiento físico y financiero de cada SKU.
    """
    __tablename__ = "wms_inventory_movements"

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
        ForeignKey("wms_inventory_documents.id"),
        index=True,
        nullable=False
    )
    
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("wms_items.id"),
        index=True,
        nullable=False
    )

    warehouse_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wms_warehouses.id"),
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

    location_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True,
        index=True,
        comment="ID de la ubicación física (Bin) en el WMS"
    )
    
    affected_stock: Mapped[bool] = mapped_column(
        Boolean, 
        default=True,
        comment="Indica si este movimiento debe impactar el stock actual"
    )

    # --- 💰 FINANZAS (Instrucción 2026-02-09) ---
    # Precios indicados basados en compañía y almacén
    _purchase_amount: Mapped[Decimal] = mapped_column(
        "_purchase_amount", Numeric(18, 4), default=0, comment="Monto unitario de compra"
    )
    _purchase_currency: Mapped[str] = mapped_column(
        "_purchase_currency", String(3), default="USD"
    )
    purchase_price: Mapped[Money] = composite(Money, _purchase_amount, _purchase_currency)

    _sell_amount: Mapped[Decimal] = mapped_column(
        "_sell_amount", Numeric(18, 4), default=0, comment="Monto unitario de venta"
    )
    _sell_currency: Mapped[str] = mapped_column(
        "_sell_currency", String(3), default="USD"
    )
    sell_price: Mapped[Money] = composite(Money, _sell_amount, _sell_currency)

    _total_amount: Mapped[Decimal] = mapped_column(
        "_total_amount", Numeric(18, 4), default=0, comment="Total monto (quantity * price)"
    )
    _total_currency: Mapped[str] = mapped_column(
        "_total_currency", String(3), default="USD"
    )
    total_line: Mapped[Money] = composite(Money, _total_amount, _total_currency)

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
    
    product: Mapped["Item"] = relationship("Item")

    # --- 🔒 CONSTRAINTS ---
    __table_args__ = (
        # Unicidad: No pueden haber dos líneas con el mismo número en un documento
        Index("ix_mov_doc_sequence", "document_id", "sequence_number", unique=True),
    )