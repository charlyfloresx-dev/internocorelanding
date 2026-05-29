import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

if TYPE_CHECKING:
    from .production_area import ProductionArea


class Facility(MultiTenantBase):
    """Planta física — raíz de la jerarquía Facility → ProductionArea → Resource."""
    __tablename__ = "mes_facilities"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_facility_company_code"),
    )

    code: Mapped[str] = mapped_column(String(25), index=True)
    name: Mapped[str] = mapped_column(String(100))
    location_description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    areas: Mapped[list["ProductionArea"]] = relationship(
        "ProductionArea", back_populates="facility", lazy="selectin"
    )
