import uuid
from datetime import time
from typing import Optional
from sqlalchemy import String, Time, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .shift import Shift


class ShiftBreak(MultiTenantBase):
    """
    Horario de descanso individual dentro de un turno.
    Portado de Interno.HumanResource.Models.Catalog.Break + BreaksGroup.

    BreaksGroup en el legacy era una colección de Break's vinculada a un Shift.
    Aquí simplificamos: cada ShiftBreak pertenece directamente a un Shift
    (el "grupo" es implícito — todos los breaks de un shift son su grupo).
    """
    __tablename__ = "mes_shift_breaks"

    shift_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mes_shifts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Código corto identificador (legacy Break.Code max 15)
    code: Mapped[str] = mapped_column(String(15), nullable=False)
    # Etiqueta legible: "Primer descanso", "Comida", etc.
    label: Mapped[str] = mapped_column(String(50))
    # Tipo: BREAK | MEAL | MAINTENANCE  (simplifica BreakType entity del legacy)
    break_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="BREAK")

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    # Duración en minutos — almacenada para cálculos rápidos de tiempo disponible
    # (en el legacy Break.Duration era TimeSpan calculado = End - Start)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    shift: Mapped["Shift"] = relationship("Shift", back_populates="breaks")
