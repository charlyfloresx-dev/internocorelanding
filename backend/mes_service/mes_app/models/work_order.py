import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase

class WorkOrder(MultiTenantBase):
    """Orden de Trabajo (WO)."""
    __tablename__ = "mes_work_orders"

    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    item_code: Mapped[str] = mapped_column(String(100), index=True)
    
    order_quantity: Mapped[int] = mapped_column(Integer)
    manufactured_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[str] = mapped_column(String(50), default="DRAFT") # DRAFT, RELEASED, IN_PROGRESS, COMPLETED, CLOSED
    material_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # For future inventory integration
    
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    request_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
