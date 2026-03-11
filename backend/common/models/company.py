import uuid
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String
from ..infrastructure.models.base import AuditBase

class Company(AuditBase):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) 

    # --- 🏢 CLUSTER / TENANT HIERARCHY ---
    parent_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("business_groups.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")

    # Relation to BusinessGroup
    business_group: Mapped[Optional["BusinessGroup"]] = relationship(
        "BusinessGroup", 
        back_populates="companies",
        foreign_keys="Company.parent_group_id"
    )