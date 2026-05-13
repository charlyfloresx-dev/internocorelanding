from decimal import Decimal
import uuid
from datetime import date
from sqlalchemy import Integer, ForeignKey, Date, Numeric, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class HourlyProductionSnapshot(MultiTenantBase):
    """Read Model: Event-driven hourly snapshot of production vs. goal."""
    __tablename__ = "mes_hourly_production_snapshots"

    __table_args__ = (
        UniqueConstraint("resource_id", "date", "hour", "company_id", name="uq_hourly_snapshot"),
    )

    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False)
    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), nullable=False)
    
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hour: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-23
    
    goal_quantity: Mapped[int] = mapped_column(Integer, default=0)
    actual_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    # Pre-calculated efficiency (Actual / Goal)
    efficiency_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.0)
    
    # Store the item code for easy filtering on the dashboard without joins
    item_code: Mapped[str] = mapped_column(String(100), index=True)
