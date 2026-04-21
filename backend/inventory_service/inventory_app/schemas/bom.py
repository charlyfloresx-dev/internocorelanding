from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from decimal import Decimal

class BOMBase(BaseModel):
    parent_item_code: str = Field(..., max_length=100)
    component_item_code: str = Field(..., max_length=100)
    quantity: Decimal = Field(..., gt=0)
    uom: str = Field("EA", max_length=20)
    level: int = Field(1, description="BOM level depth")
    is_active: bool = True

class BOMCreate(BOMBase):
    pass

class BOMUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    uom: Optional[str] = None
    is_active: Optional[bool] = None

class BOMRead(BOMBase):
    id: UUID
    company_id: UUID

    class Config:
        from_attributes = True
