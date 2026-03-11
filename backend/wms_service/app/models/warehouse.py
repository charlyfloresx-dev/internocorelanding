from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import Base, MultiTenantBase

if TYPE_CHECKING:
    from .inventory_document import InventoryDocument
    from .inventory_snapshot import InventorySnapshot

class WarehouseType(MultiTenantBase, Base):
    __tablename__ = "warehouse_types"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

class WarehouseGroup(MultiTenantBase, Base):
    __tablename__ = "warehouse_groups"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

class Warehouse(MultiTenantBase, Base):
    """
    Traducido del legacy Warehouse.cs.
    Gestión de bodegas físicas y lógicas.
    """
    __tablename__ = "warehouses"

    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    capacity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    unit_code: Mapped[Optional[str]] = mapped_column(String(10))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Jerarquía
    warehouse_type_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouse_types.id"))
    warehouse_group_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouse_groups.id"))

    # Relationships
    warehouse_type: Mapped[Optional["WarehouseType"]] = relationship()
    warehouse_group: Mapped[Optional["WarehouseGroup"]] = relationship()
    documents: Mapped[List["InventoryDocument"]] = relationship("InventoryDocument", back_populates="warehouse", lazy="select")
    snapshots: Mapped[List["InventorySnapshot"]] = relationship("InventorySnapshot", back_populates="warehouse", lazy="select")
    zones: Mapped[List["Zone"]] = relationship("Zone", back_populates="warehouse", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_warehouse_company_code"),
    )

class Zone(MultiTenantBase, Base):
    """
    Representa una zona lógica dentro de un almacén (p.e. Recepción, Almacenamiento, Calidad).
    """
    __tablename__ = "warehouse_zones"

    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    warehouse_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    
    # Relationships
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="zones")

    __table_args__ = (
        UniqueConstraint("company_id", "warehouse_id", "code", name="uq_zone_warehouse_code"),
    )
