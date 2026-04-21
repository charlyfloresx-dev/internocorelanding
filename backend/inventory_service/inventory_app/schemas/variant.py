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
    photo_path: Optional[str] = None
    product_url: Optional[str] = None # Virtual field for frontend
    
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
    photo_path: Optional[str] = None

class VariantListResponse(BaseModel):
    status: str = "success"
    data: List[ItemVariantRead]
