from decimal import Decimal
from pydantic import BaseModel, Field
from uuid import UUID

from typing import Optional
from wms_app.domain.entities.sales_order import SalesOrderStatus

class SalesOrderBase(BaseModel):
    folio: str
    observations: Optional[str] = None

class SalesOrderCreate(SalesOrderBase):
    product_id: UUID
    warehouse_id: UUID
    uom_id: UUID
    quantity: Decimal = Field(..., gt=0)

class SalesOrderRead(SalesOrderBase):
    id: UUID

    status: SalesOrderStatus
    product_id: UUID
    warehouse_id: UUID
    uom_id: UUID
    quantity: Decimal
    total_items: int

    class Config:
        from_attributes = True
