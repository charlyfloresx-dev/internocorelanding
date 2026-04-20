from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
import uuid

class LocationBase(BaseModel):
    code: str = Field(..., max_length=50)
    max_capacity: Decimal = Field(default=Decimal("0.0"), decimal_places=4)
    zone: Optional[str] = Field(None, max_length=50)

class LocationCreate(LocationBase):
    warehouse_id: uuid.UUID

class LocationResponse(LocationBase):
    id: uuid.UUID
    warehouse_id: uuid.UUID
    company_id: uuid.UUID

    class Config:
        from_attributes = True

class LocationCapacityResponse(BaseModel):
    location_id: uuid.UUID
    code: str
    max_capacity: Decimal
    warehouse_id: uuid.UUID
