import uuid
from datetime import time
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

if TYPE_CHECKING:
    pass


class BreakSlot(MultiTenantBase):
    """
    Franja de descanso dentro de un grupo — define CUÁNDO y para CUÁNTOS
    trabajadores aplica este horario de break.

    Múltiples slots por grupo permiten escalonar turnos (ej. Turno A: 9:00-9:30,
    Turno B: 9:30-10:00) para evitar saturar áreas comunes (baños, cafetería).
    """
    __tablename__ = "hcm_break_slots"

    break_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hcm_break_groups.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    break_type: Mapped[str] = mapped_column(String(20), nullable=False, default="BREAK")
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    max_concurrent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    break_group: Mapped["BreakGroup"] = relationship("BreakGroup", back_populates="slots")


class BreakGroup(MultiTenantBase):
    """
    Grupo de descanso HCM — agrupa franjas horarias escalonadas para una zona de planta.
    La capacidad del área limita cuántos trabajadores pueden tomar descanso al mismo tiempo.

    Resource.break_group_id (soft FK en MES) apunta a este ID.
    ResourceGraphicService consume HTTP /hcm/break-groups/{id}/slots para obtener
    los breaks reales cuando break_group_id != NULL.
    """
    __tablename__ = "hcm_break_groups"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    area_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
                                                comment="Capacidad máxima del área común (baños/cafetería)")

    slots: Mapped[list["BreakSlot"]] = relationship(
        "BreakSlot",
        back_populates="break_group",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="BreakSlot.start_time",
    )
