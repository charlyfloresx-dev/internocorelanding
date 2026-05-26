import uuid
from datetime import time
from typing import Optional
from sqlalchemy import String, Time, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class Shift(MultiTenantBase):
    """
    AL-005: Definición de turnos de trabajo.
    Soporta resolución jerárquica y cruce de medianoche.
    """
    __tablename__ = "mes_shifts"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))

    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    # True when the shift ends the following calendar day (e.g. 22:00 → 06:00)
    is_overnight: Mapped[bool] = mapped_column(Boolean, default=False)

    # Total scheduled break time in minutes (lunch + rest breaks).
    # Used by ShiftService.calculate_available_minutes() to compute net productive time.
    # Default 60 min matches the legacy Interno.HumanResource TotalTimeBreaks value.
    break_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Hierarchy: optional resource-level override
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_resources.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
