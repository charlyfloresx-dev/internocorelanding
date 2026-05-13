from decimal import Decimal
import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

from inventory_app.domain.entities.customs import CustomsOperationType

class CustomsPedimento(MultiTenantBase):
    """
    Independent entity representing a Customs Declaration (Pedimento).
    Essential for Anexo 24/30 FIFO traceability.
    """
    __tablename__ = "customs_pedimentos"

    pedimento_number: Mapped[str] = mapped_column(String(15), unique=True, index=True, nullable=False)
    customs_key: Mapped[str] = mapped_column(String(10), nullable=False) # e.g., IN, AF, RT, V1
    operation_type: Mapped[CustomsOperationType] = mapped_column(Enum(CustomsOperationType), nullable=False)
    customs_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Financial fields for customs compliance
    exchange_rate_dof: Mapped[Optional[Decimal]] = mapped_column(nullable=True)
    
    comments: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<CustomsPedimento(number={self.pedimento_number}, key={self.customs_key}, date={self.customs_date})>"
