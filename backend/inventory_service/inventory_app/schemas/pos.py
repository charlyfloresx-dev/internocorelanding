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
    customer_id: Optional[uuid.UUID] = None
    partner_id: Optional[uuid.UUID] = None  # mobile alias for customer_id
    total_amount: Decimal
    currency: str = "MXN"
    payment_method: Optional[str] = None
    app_reference: Optional[str] = None

    def model_post_init(self, __context) -> None:
        if self.customer_id is None and self.partner_id is not None:
            object.__setattr__(self, 'customer_id', self.partner_id)

class SaleResponse(BaseModel):
    sale_id: uuid.UUID
    status: str = "COMPLETED"
    movement_ids: List[uuid.UUID]
