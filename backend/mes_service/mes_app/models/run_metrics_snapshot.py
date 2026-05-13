from decimal import Decimal
import uuid
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class RunMetricsSnapshot(MultiTenantBase):
    """Immutable Read Model tracking final performance KPIs for closed runs."""
    __tablename__ = "mes_run_metrics_snapshots"
    
    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), unique=True, nullable=False)
    
    availability: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0.0) # E.g. 0.95 (95%)
    efficiency: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0.0)
    quality: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0.0)
    oee: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0.0)
    
    tak_time_seconds: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0.0)
    lmpu_minutes: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0.0) # Labor Minutes Per Unit
