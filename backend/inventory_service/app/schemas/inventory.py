import uuid
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

from app.models.inventory import TransactionType

class InventoryTransactionCreate(BaseModel):
    product_id: uuid.UUID
    uom_id: uuid.UUID
    warehouse_id: uuid.UUID
    transaction_type: TransactionType
    quantity_change: float = Field(..., description="Amount to add (positive) or remove (negative, handled by logic usually positive magnitude with OUT type)")
    unit_cost: Optional[float] = Field(0.0, description="Cost of the unit for CPP calculation (only for IN)")
    fulfill_reservation: bool = False
    reference_id: Optional[uuid.UUID] = None
    comments: Optional[str] = None

class InventoryLevelRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    uom_id: uuid.UUID
    quantity: float
    reserved_quantity: float
    weighted_average_cost: float
    last_purchase_price: float
    replacement_price: float
    currency_code: str
    version_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class InventoryTransactionRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    transaction_type: TransactionType
    quantity_change: float
    previous_balance: float
    new_balance: float
    reference_id: Optional[uuid.UUID]
    comments: Optional[str] = None
    created_at: datetime
    created_by: Optional[uuid.UUID]
    transaction_id: Optional[uuid.UUID]

    model_config = ConfigDict(from_attributes=True)
