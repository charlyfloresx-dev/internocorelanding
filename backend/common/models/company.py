import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from ..infrastructure.models.base import AuditBase

if TYPE_CHECKING:
    from .business_group import BusinessGroup

class Company(AuditBase):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) 
    country_code: Mapped[str] = mapped_column(String(2), default="MX", nullable=False) # ISO 3166-1 alpha-2

    # --- 🏢 CLUSTER / TENANT HIERARCHY ---
    parent_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("business_groups.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    
    # ── CURRENCY CONFIGURATION ──────────────────────────────────────────────
    base_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Relation to BusinessGroup
    business_group: Mapped[Optional["BusinessGroup"]] = relationship(
        "BusinessGroup", 
        back_populates="companies",
        foreign_keys="Company.parent_group_id"
    )