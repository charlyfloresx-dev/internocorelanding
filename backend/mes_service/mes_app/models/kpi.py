import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

class Goal(MultiTenantBase):
    """Meta horaria por recurso."""
    __tablename__ = "mes_goals"

    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False)
    hour_of_day: Mapped[int] = mapped_column(Integer) # 0-23
    target_qty: Mapped[int] = mapped_column(Integer)

