import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

if TYPE_CHECKING:
    from .facility import Facility
    from .resource import Resource


class ProductionArea(MultiTenantBase):
    """Zona dentro de una planta — contiene uno o más Resources."""
    __tablename__ = "mes_production_areas"
    __table_args__ = (
        UniqueConstraint("company_id", "name", "facility_id", name="uq_area_company_name_facility"),
    )

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("mes_facilities.id", ondelete="SET NULL"), nullable=True, index=True
    )

    facility: Mapped[Optional["Facility"]] = relationship("Facility", back_populates="areas")
    resources: Mapped[list["Resource"]] = relationship("Resource", back_populates="production_area", lazy="selectin")
