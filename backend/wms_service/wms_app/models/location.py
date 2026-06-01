import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, UniqueConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from common.models import MultiTenantBase

class LocationType(str, enum.Enum):
    RECEIVING = "RECEIVING"
    PICKING = "PICKING"
    OVERSTOCK = "OVERSTOCK"
    RECURSO = "RECURSO"      # For machines/WIP resources
    QUALITY = "QUALITY"      # For quarantine/inspection

class Location(MultiTenantBase):
    __tablename__ = "locations"

    warehouse_id = Column(UUID(as_uuid=True), ForeignKey("wms_warehouses.id"), nullable=False, index=True)
    parent_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True)
    
    zone_code = Column(String(50), nullable=False)
    bin_code = Column(String(50), nullable=False)
    
    type = Column(Enum(LocationType), nullable=False, default=LocationType.PICKING)
    is_active = Column(Boolean, default=True)
    
    # Industrial Capacity Monitoring
    max_capacity = Column(Numeric(18, 4), nullable=True, default=0.0)
    current_capacity = Column(Numeric(18, 4), nullable=True, default=0.0)

    __table_args__ = (
        UniqueConstraint("company_id", "warehouse_id", "zone_code", "bin_code", name="uq_location_coords"),
    )

    def __repr__(self):
        return f"<Location(id={self.id}, type={self.type}, code={self.zone_code}-{self.bin_code})>"
