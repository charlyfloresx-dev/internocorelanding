import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Integer, Float, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

class Goal(MultiTenantBase):
    """Meta horaria por recurso."""
    __tablename__ = "mes_goals"

    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False)
    hour_of_day: Mapped[int] = mapped_column(Integer) # 0-23
    target_qty: Mapped[int] = mapped_column(Integer)

class HourByHour(MultiTenantBase):
    """Reporte granular Meta vs Real por hora."""
    __tablename__ = "mes_hour_by_hour"

    resource_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resource_results.id"), nullable=False)
    hour_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    sku: Mapped[Optional[str]] = mapped_column(String(100))
    meta_qty: Mapped[int] = mapped_column(Integer, default=0)
    actual_qty: Mapped[int] = mapped_column(Integer, default=0)
    
    std_time: Mapped[float] = mapped_column(Float, default=0.0)
    operators_qty: Mapped[int] = mapped_column(Integer, default=0)
    
    @property
    def attainment_pct(self) -> float:
        if self.meta_qty <= 0:
            return 0.0
        return (self.actual_qty / self.meta_qty) * 100

    @property
    def efficiency_pct(self) -> float:
        # Lógica legacy: (Pieces * StdTime) / PaidHrs
        # Aquí simplificamos o portamos según sea necesario
        return 0.0
