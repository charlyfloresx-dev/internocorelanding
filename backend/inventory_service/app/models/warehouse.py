import uuid
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

from common.models import BaseWarehouse

class Warehouse(BaseWarehouse):
    """
    Local representation of a warehouse for inventory management.
    """
    __tablename__ = "inventory_warehouses"

    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_transit: Mapped[bool] = mapped_column(default=False)

    def __repr__(self):
        return f"<Warehouse(code={self.code}, name={self.name})>"
