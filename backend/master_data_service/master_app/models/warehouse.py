import uuid
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase
import enum

class WarehouseType(str, enum.Enum):
    PHYSICAL = "PHYSICAL"
    VIRTUAL = "VIRTUAL"
    TRANSIT = "TRANSIT"
    RESOURCE = "RESOURCE"  # Machine/station acting as WIP warehouse

from common.models import BaseWarehouse

class Warehouse(BaseWarehouse, MultiTenantBase):
    __tablename__ = "warehouses"

    # MVP: structure ready for capacity enforcement (Hard Cap future phase)
    is_production_resource: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<Warehouse(code='{self.code}', name='{self.name}', country='{self.country_code}', type='{self.type}')>"
