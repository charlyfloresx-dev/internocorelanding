import uuid
from typing import Optional
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class LaborAllocation(MultiTenantBase):
    """Tracks how many operators were working on a specific shift/run."""
    __tablename__ = "mes_labor_allocations"
    
    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), nullable=False)
    operator_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    collaborator_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    shift_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
