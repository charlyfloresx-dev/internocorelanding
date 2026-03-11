import uuid
from typing import Optional
from sqlalchemy import String, Float, UniqueConstraint, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from common.models import MultiTenantBase

class Item(MultiTenantBase):
    __tablename__ = "items"

    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Propiedades espec\u00edficas del WMS legacy si son necesarias
    sku: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    stock_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    bin_location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_item_company_code'),
    )