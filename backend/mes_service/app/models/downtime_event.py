import uuid
from typing import Optional
from sqlalchemy import Integer, ForeignKey, String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from common.models.base_models import MultiTenantBase

class DowntimeEvent(MultiTenantBase):
    """Tracks scheduled breaks and unexpected downtimes."""
    __tablename__ = "mes_downtime_events"
    
    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # High precision numeric for exact minutes
    duration_minutes: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    
    # Flag to differentiate between actual issues and planned breaks (e.g., lunch)
    is_planned: Mapped[bool] = mapped_column(Boolean, default=False)
