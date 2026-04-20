import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

if TYPE_CHECKING:
    from .production_run import ProductionRun

class DowntimeReason(MultiTenantBase):
    """Catálogo de razones de paro (Issues)."""
    __tablename__ = "mes_downtime_reasons"

    code: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50)) # Mantenimiento, Calidad, etc.

class Downtime(MultiTenantBase):
    """Registro de paros (Issues de piso)."""
    __tablename__ = "mes_downtimes"

    guid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), nullable=False)
    reason_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_downtime_reasons.id"), nullable=True)
    
    request_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True) # Quién reportó el paro
    assign_to_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True) # Técnico asignado
    admin_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True) # Supervisor que realiza el cierre administrativo
    
    description: Mapped[Optional[str]] = mapped_column(String(500))
    action_taken: Mapped[Optional[str]] = mapped_column(String(500))
    root_cause: Mapped[Optional[str]] = mapped_column(String(500)) # Causas raíz para el cierre administrativo
    
    status: Mapped[str] = mapped_column(String(20), default="OPEN") # OPEN, RESPONDED, TECH_CLOSED, ADMIN_CLOSED
    
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    admin_closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    escalation_level: Mapped[int] = mapped_column(default=0)
    last_escalation_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    production_run: Mapped["ProductionRun"] = relationship(back_populates="downtimes")
    reason: Mapped[Optional["DowntimeReason"]] = relationship()

    @property
    def mttr_minutes(self) -> float:
        """Mean Time To Repair (Desde el inicio hasta el cierre técnico)."""
        end = self.closed_at or datetime.now()
        return (end - self.start_at).total_seconds() / 60

    @property
    def response_time_minutes(self) -> float:
        """Tiempo que tardó el soporte en llegar."""
        if not self.responded_at:
            return (datetime.now() - self.start_at).total_seconds() / 60
        return (self.responded_at - self.start_at).total_seconds() / 60
