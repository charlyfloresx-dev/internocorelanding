from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field
import enum

class TransactionType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    BACKFLUSHING = "BACKFLUSHING"

class InventoryLevelEntity(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    uom_id: UUID
    quantity: Decimal
    reserved_quantity: Decimal
    weighted_average_cost: Decimal
    last_purchase_price: Decimal
    replacement_price: Decimal
    currency_code: str
    company_id: UUID

class InventoryTransactionEntity(BaseModel):
    id: UUID
    product_id: UUID
    warehouse_id: UUID
    transaction_type: TransactionType
    quantity_change: Decimal
    previous_balance: Decimal
    new_balance: Decimal
    reference_id: Optional[UUID] = None
    comments: Optional[str] = None
    company_id: UUID

class InventoryLineEntity(BaseModel):
    product_id: UUID
    quantity: Decimal
    warehouse_id: UUID
    uom_id: Optional[UUID] = None # Or inferred

class InventoryDocumentEntity(BaseModel):
    id: UUID
    document_type: str
    status: str
    movement_type: TransactionType
    lines: List[InventoryLineEntity]
    company_id: UUID

class MovementEntity(BaseModel):
    id: UUID
    warehouse_id: UUID
    product_id: UUID
    company_id: UUID
    quantity: Decimal
    movement_type: str
    document_type: str
    document_id: UUID
