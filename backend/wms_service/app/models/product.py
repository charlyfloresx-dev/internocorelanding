from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from common.models import Base, MultiTenantBase

class Product(MultiTenantBase, Base):
    """
    Traducido del legacy Item.cs.
    Representa un artículo almacenable con propiedades de planeación y logística.
    """
    __tablename__ = "products"

    code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    alias: Mapped[Optional[str]] = mapped_column(String(100))
    revision: Mapped[Optional[str]] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Planeación (Numeric 18,4)
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    reorder_point: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    min_order_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    max_order_qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    order_multiple: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=1)

    # Logística (Numeric 18,4)
    weight: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    length: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    width: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    height: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    unit_code: Mapped[Optional[str]] = mapped_column(String(10))

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_product_company_code"),
    )