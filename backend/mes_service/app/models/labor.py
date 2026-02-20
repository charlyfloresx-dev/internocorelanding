import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models.base_models import MultiTenantBase

class LaborType(MultiTenantBase):
    """Tipos de registros de labor (ej. Directo, Indirecto, Calidad)."""
    __tablename__ = "mes_labor_types"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

class Labor(MultiTenantBase):
    """Rastreo de personal en línea (Labor Tracking)."""
    __tablename__ = "mes_labors"

    resource_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resource_results.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False) # ID universal del usuario
    employee_number: Mapped[Optional[int]] = mapped_column(nullable=True) # Número de gafete (Legacy)
    
    clock_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active_labor: Mapped[bool] = mapped_column(Boolean, default=True)
    
    type_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_labor_types.id"), nullable=True)
    labor_type: Mapped[Optional["LaborType"]] = relationship()

    # Relaciones
    production_result: Mapped["ResourceResult"] = relationship(back_populates="labors")

    @property
    def transcurred_minutes(self) -> float:
        end = self.clock_out or datetime.now()
        return (end - self.clock_in).total_seconds() / 60
