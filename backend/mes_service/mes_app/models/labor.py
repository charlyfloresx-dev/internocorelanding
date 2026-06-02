import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

if TYPE_CHECKING:
    from .production_run import ProductionRun

class LaborType(MultiTenantBase):
    """Tipos de registros de labor (ej. Directo, Indirecto, Calidad)."""
    __tablename__ = "mes_labor_types"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

class Labor(MultiTenantBase):
    """Rastreo de personal en línea (Labor Tracking)."""
    __tablename__ = "mes_labors"

    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False) # ID universal del usuario
    employee_number: Mapped[Optional[int]] = mapped_column(nullable=True) # Número de gafete (Legacy)
    
    clock_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active_labor: Mapped[bool] = mapped_column(Boolean, default=True)

    collaborator_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    collaborator_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    assigned_plant: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_deviation: Mapped[bool] = mapped_column(Boolean, default=False)
    
    type_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_labor_types.id"), nullable=True)
    labor_type: Mapped[Optional["LaborType"]] = relationship()

    # Relaciones
    production_run: Mapped["ProductionRun"] = relationship(back_populates="labors")

    @property
    def transcurred_minutes(self) -> float:
        end = self.clock_out or datetime.now()
        return (end - self.clock_in).total_seconds() / 60

    @property
    def resource_result_id(self) -> uuid.UUID:
        return self.production_run_id

    @resource_result_id.setter
    def resource_result_id(self, value: uuid.UUID) -> None:
        self.production_run_id = value
