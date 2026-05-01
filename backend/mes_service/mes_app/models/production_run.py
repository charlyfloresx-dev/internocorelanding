import uuid
from datetime import date
from sqlalchemy import Integer, ForeignKey, Date, UniqueConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from common.models import MultiTenantBase

if TYPE_CHECKING:
    from .ledger import ManufacturingLedger
    from .labor import Labor
    from .downtime import Downtime

class ProductionRun(MultiTenantBase):
    __tablename__ = "mes_production_runs"
    
    __table_args__ = (
        UniqueConstraint("resource_id", "date", "shift_id", "company_id", name="uq_production_run_schedule"),
    )

    work_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_work_orders.id"), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False)
    shift_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    
    date: Mapped[date] = mapped_column(Date, nullable=False)
    leader_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supervisor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    planned_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_quantity: Mapped[int] = mapped_column(Integer, default=0)

    ledger_entries: Mapped[List["ManufacturingLedger"]] = relationship(back_populates="production_run")
    labors: Mapped[List["Labor"]] = relationship(back_populates="production_run")
    downtimes: Mapped[List["Downtime"]] = relationship(back_populates="production_run")
