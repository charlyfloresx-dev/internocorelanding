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
    
    # Si True, el turno termina el día siguiente al que inició (ej. 22:00 -> 06:00)
    is_overnight: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Jerarquía: Opcionales para permitir herencia
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_resources.id"), nullable=True)
    facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_facilities.id"), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
