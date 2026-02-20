import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Integer, Numeric, Interval
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models.base_models import MultiTenantBase

class Rout(MultiTenantBase):
    """Ruta de manufactura (Master)."""
    __tablename__ = "mes_routs"

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    revision: Mapped[str] = mapped_column(String(10))
    
    operations: Mapped[List["OperationTime"]] = relationship(back_populates="rout")

class OperationTime(MultiTenantBase):
    """Tiempo estándar de operación por producto/proceso."""
    __tablename__ = "mes_operation_times"

    guid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    rout_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_routs.id"), nullable=True)
    
    product_sku: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(250))
    operation_name: Mapped[str] = mapped_column(String(100))
    
    operators_needed: Mapped[int] = mapped_column(Integer, default=1)
    run_time: Mapped[timedelta] = mapped_column(Interval) # TimeSpan en .NET
    set_time: Mapped[timedelta] = mapped_column(Interval)
    
    cost: Mapped[Optional[float]] = mapped_column(default=0.0)

    rout: Mapped[Optional["Rout"]] = relationship(back_populates="operations")

class WorkOrder(MultiTenantBase):
    """Orden de Trabajo (WO)."""
    __tablename__ = "mes_work_orders"

    order_number: Mapped[str] = mapped_column(String(50), primary_key=True)
    guid: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True)
    
    item_code: Mapped[str] = mapped_column(String(100), index=True)
    alias: Mapped[Optional[str]] = mapped_column(String(100))
    
    order_qty: Mapped[int] = mapped_column(Integer)
    manufactured_qty: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[str] = mapped_column(String(20), default="RELEASED") # Released, Completed, Closed
    
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finish_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    operation_time_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_operation_times.id"), nullable=True)
    rout_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_routs.id"), nullable=True)

    @property
    def missing_qty(self) -> int:
        return max(0, self.order_qty - self.manufactured_qty)
