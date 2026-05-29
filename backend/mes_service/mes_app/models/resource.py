import uuid
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

if TYPE_CHECKING:
    from .production_area import ProductionArea
    from .resource_support_member import ResourceSupportMember
    from .shift import Shift


class Resource(MultiTenantBase):
    """
    Work Center / Production Line — celda, máquina, área o línea de producción.

    Corresponde a Interno.Production.Resource que heredaba Warehouse en el .NET legacy.
    En Python (Iron Wall ADR-02) NO hereda de Warehouse: usa warehouse_id como soft FK
    que apunta a inventory_service.warehouses.id sin constraint de BD.
    """
    __tablename__ = "mes_resources"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_resource_company_code"),
    )

    # Clave de negocio — max 13 chars para paridad con legacy Warehouse.Code
    code: Mapped[str] = mapped_column(String(13), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    # CELL | MACHINE | AREA | LINE  (string enum — simple y extensible)
    resource_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    # Capacidad en piezas/hora (del legacy Warehouse.Capacity — float en .NET, Decimal aquí)
    capacity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Soft FK → inventory_service.warehouses.id  (Iron Wall: sin FK constraint de BD)
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Jerarquía de planta
    production_area_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("mes_production_areas.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Break group (legacy BreakGroupId) — soft FK hacia hcm_service
    break_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True)

    production_area: Mapped[Optional["ProductionArea"]] = relationship(
        "ProductionArea", back_populates="resources"
    )
    support_members: Mapped[list["ResourceSupportMember"]] = relationship(
        "ResourceSupportMember", back_populates="resource", cascade="all, delete-orphan", lazy="selectin"
    )
    shifts: Mapped[list["Shift"]] = relationship(
        "Shift", back_populates="resource", lazy="selectin"
    )
