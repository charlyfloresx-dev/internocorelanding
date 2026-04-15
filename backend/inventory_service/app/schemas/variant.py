import uuid
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class ItemVariantRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    internal_sku: str
    brand: str
    mfg_part_number: str
    unit_price: Decimal
    weight: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    is_preferred: bool
    
    model_config = ConfigDict(from_attributes=True)

class ItemVariantCreate(BaseModel):
    product_id: uuid.UUID
    internal_sku: str
    brand: str = Field(..., description="Brand or Supplier Name")
    mfg_part_number: str = Field(..., description="Manufacturer Part Number")
    unit_price: Decimal = Decimal("0.0")
    weight: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    is_preferred: bool = False

class VariantListResponse(BaseModel):
    status: str = "success"
    data: List[ItemVariantRead]
