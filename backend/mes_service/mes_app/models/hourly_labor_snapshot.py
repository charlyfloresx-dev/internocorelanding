from decimal import Decimal
import uuid
from datetime import date
from sqlalchemy import Integer, ForeignKey, Date, Numeric, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase


class HourlyLaborSnapshot(MultiTenantBase):
    """Read Model: Time-sliced headcount and labor density per resource per hour.

    Materialized by LaborDensityService on every clock_in, clock_out, and transfer event.
    Supports O(1) supervisor dashboard queries ('cuántos colaboradores a las 7AM?').

    Estado subdividido:
      - headcount_active: productivos, cuentan para capacidad del recurso
      - headcount_on_permit: en permiso autorizado, visibles para supervisor
      - headcount_transferred_in: llegaron de otro recurso este intervalo
      - headcount_transferred_out: salieron a otro recurso este intervalo
    """
    __tablename__ = "mes_hourly_labor_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "resource_id", "date", "hour", "company_id",
            name="uq_resource_hourly_labor",
        ),
        Index("ix_hourly_labor_resource_date", "resource_id", "date"),
    )

    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False)
    production_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_production_runs.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    hour: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–23

    # Estado subdividido (resolución de negocio acordada)
    headcount_active: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    headcount_on_permit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    headcount_transferred_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    headcount_transferred_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Tiempo efectivo dentro de esta hora
    total_labor_minutes: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    paid_hrs: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
    # gained_hrs se actualiza por eventos de producción (piezas × std_time), no por labor events
    gained_hrs: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("0"), nullable=False)
