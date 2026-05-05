from pydantic import BaseModel, Field
from typing import Optional
import uuid

class WarehouseBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=250)
    type: str = Field("PHYSICAL", max_length=50) # PHYSICAL, VIRTUAL, TRANSIT
    country_code: str = Field("MX", max_length=2)
    is_active: bool = True

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=250)
    type: Optional[str] = Field(None, max_length=50)
    country_code: Optional[str] = Field(None, max_length=2)
    is_active: Optional[bool] = None

class WarehouseResponse(WarehouseBase):
    id: uuid.UUID
    company_id: uuid.UUID

    class Config:
        from_attributes = True
