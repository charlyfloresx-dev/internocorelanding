import uuid
from typing import Optional
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from common.models.base_models import MultiTenantBase

class LaborAllocation(MultiTenantBase):
    """Tracks how many operators were working on a specific shift/run."""
    __tablename__ = "mes_labor_allocations"
    
    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), nullable=False)
    operator_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
