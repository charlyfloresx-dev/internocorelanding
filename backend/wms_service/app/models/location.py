import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from common.models import MultiTenantBase

class LocationType(str, enum.Enum):
    RECEIVING = "RECEIVING"
    PICKING = "PICKING"
    OVERSTOCK = "OVERSTOCK"

class Location(MultiTenantBase):
    __tablename__ = "locations"

    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False, index=True)
    zone_code = Column(String(50), nullable=False)
    bin_code = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    type = Column(Enum(LocationType), nullable=False, default=LocationType.PICKING)

    __table_args__ = (
        UniqueConstraint("company_id", "warehouse_id", "zone_code", "bin_code", name="uq_location_coords"),
    )

    def __repr__(self):
        return f"<Location(id={self.id}, warehouse_id={self.warehouse_id}, code={self.zone_code}-{self.bin_code})>"
