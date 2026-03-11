import uuid
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field

class VariantSearchResult(BaseModel):
    display_name: str = Field(..., description="Formatted name: SKU | Brand MPN (Warehouse)")
    sku_maestro: str = Field(..., description="Internal Item SKU")
    variant_id: uuid.UUID
    brand: str
    mfg_part_number: str
    quantity: Decimal = Field(default=Decimal("0.0"), description="Available stock in warehouse")
    weight: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    warehouse_name: str

class VariantSearchResponse(BaseModel):
    status: str = "success"
    data: List[VariantSearchResult]
