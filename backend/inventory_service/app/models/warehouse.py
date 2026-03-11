import uuid
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

class Warehouse(MultiTenantBase):
    """
    Local representation of a warehouse for inventory management.
    """
    __tablename__ = "inventory_warehouses"

    code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    def __repr__(self):
        return f"<Warehouse(code={self.code}, name={self.name})>"
