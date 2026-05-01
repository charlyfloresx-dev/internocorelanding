import uuid
from typing import Optional
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class Resource(MultiTenantBase):
    """Work Center / Production Line."""
    __tablename__ = "mes_resources"

    code: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Optional grouping for breaks, should align with company's HR/Shift configuration.
    break_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
