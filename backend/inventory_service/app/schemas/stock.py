from pydantic import BaseModel, Field
from decimal import Decimal
import uuid
from typing import Optional

class StockBase(BaseModel):
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal = Field(default=0)
    reserved_quantity: Decimal = Field(default=0)

class StockRead(StockBase):
    id: uuid.UUID
    company_id: uuid.UUID

    class Config:
        from_attributes = True

class MovementCreate(BaseModel):
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    movement_type: str # IN, OUT, ADJUSTMENT
    document_type: str
    document_id: uuid.UUID

class StockReserveCmd(BaseModel):
    warehouse_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal

class TransferDispatchCmd(BaseModel):
    from_warehouse_id: uuid.UUID
    to_warehouse_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    transfer_id: uuid.UUID

class TransferReceiveCmd(BaseModel):
    from_warehouse_id: uuid.UUID
    to_warehouse_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    transfer_id: uuid.UUID
