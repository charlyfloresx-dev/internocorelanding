import uuid
from typing import Optional, List
from sqlalchemy import String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_models import AuditBase

class Company(AuditBase):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) 

    # --- 🏢 CLUSTER / TENANT HIERARCHY ---
    parent_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")