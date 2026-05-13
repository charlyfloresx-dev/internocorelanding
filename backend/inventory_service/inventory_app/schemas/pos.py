import uuid
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Optional
from common.domain.value_objects import Money

class SaleItemCreate(BaseModel):
    product_id: uuid.UUID
    sku: str
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=Decimal("0.0"))
    currency: str = "MXN"
    is_taxable: bool = True

class SaleCreate(BaseModel):
    items: List[SaleItemCreate]
    warehouse_id: uuid.UUID
    comments: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None # Optional for POS
    total_amount: Decimal
    currency: str = "MXN"

class SaleResponse(BaseModel):
    sale_id: uuid.UUID
    status: str = "COMPLETED"
    movement_ids: List[uuid.UUID]
