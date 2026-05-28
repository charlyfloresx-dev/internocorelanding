from sqlalchemy import Numeric
from decimal import Decimal
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
    
    # ── CURRENCY & TAX CONFIGURATION ──────────────────────────────────────────
    base_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    default_tax_rate: Mapped[Decimal] = mapped_column(default=0.16)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Collaborator ID validation regex (optional, per-company)
    # e.g. "^EMP-\\d{4}$" — enforced at collaborator login before HCM lookup
    internal_id_pattern: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Relation to BusinessGroup
    business_group: Mapped[Optional["BusinessGroup"]] = relationship(
        "BusinessGroup", 
        back_populates="companies",
        foreign_keys="Company.parent_group_id"
    )