from decimal import Decimal
import uuid
from typing import Optional
from sqlalchemy import String, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class StandardTime(MultiTenantBase):
    """Standard routing/operation time for a product."""
    __tablename__ = "mes_standard_times"

    item_code: Mapped[str] = mapped_column(String(100), index=True)
    operation_name: Mapped[str] = mapped_column(String(100))

    # Position of this operation within the item's manufacturing route.
    # Use multiples of 10 (10, 20, 30…) to allow inserting steps between existing ones.
    sequence_number: Mapped[int] = mapped_column(Integer, default=10, server_default='10')

    # Machine/operator setup time in hours (legacy: OperationTime.SetTime)
    set_time_hours: Mapped[Decimal] = mapped_column(Numeric(10, 4))

    # Machine cycle time per piece in seconds (legacy: OperationTime.RunTime).
    # When populated, ManufacturingMath uses this for TakTime and theoretical capacity.
    # NULL means the operation has not been time-studied yet; fallback to set_time_hours.
    cycle_time_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
