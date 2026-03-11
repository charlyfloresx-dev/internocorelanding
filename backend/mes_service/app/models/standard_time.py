import uuid
from typing import Optional
from sqlalchemy import String, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from common.models.base_models import MultiTenantBase

class StandardTime(MultiTenantBase):
    """Standard routing/operation time for a product."""
    __tablename__ = "mes_standard_times"

    item_code: Mapped[str] = mapped_column(String(100), index=True)
    operation_name: Mapped[str] = mapped_column(String(100))
    
    # Numeric 10,4 to capture precise minutes/seconds in hours without float rounding errors
    set_time_hours: Mapped[float] = mapped_column(Numeric(10, 4))
