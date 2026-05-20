from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel


class DocumentLineRead(BaseModel):
    product_id: uuid.UUID
    product_name: str
    sku: str
    transaction_type: str
    quantity: Decimal
    unit_price: Optional[Decimal]
    currency: str
    line_total: Optional[Decimal]

    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: uuid.UUID
    folio: str
    document_type: str
    status: str
    origin_name: Optional[str]
    destination_name: Optional[str]
    total_items: int
    total_amount: Decimal
    total_currency: str
    created_at: datetime
    items: List[DocumentLineRead]

    model_config = {"from_attributes": True}
