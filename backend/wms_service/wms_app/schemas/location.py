from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

from ..models.location import LocationType

class LocationBase(BaseModel):
    warehouse_id: UUID
    zone_code: str = Field(..., max_length=50)
    bin_code: str = Field(..., max_length=50)
    type: LocationType = LocationType.PICKING
    is_active: bool = True

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    zone_code: Optional[str] = Field(None, max_length=50)
    bin_code: Optional[str] = Field(None, max_length=50)
    type: Optional[LocationType] = None
    is_active: Optional[bool] = None

class LocationResponse(LocationBase):
    id: UUID
    company_id: UUID

    class Config:
        from_attributes = True
