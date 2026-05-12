import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Union
from datetime import datetime
from decimal import Decimal

from inventory_app.domain.entities.inventory_item import TransactionType


def _sanitize_uuid_field(v):
    """Convert empty strings or invalid values to None for optional UUID fields."""
    if v is None:
        return None
    if isinstance(v, str) and not v.strip():
        return None
    return v


class InventoryTransactionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    product_id: Union[uuid.UUID, str]
    uom_id: Optional[Union[uuid.UUID, str]] = None
    warehouse_id: Union[uuid.UUID, str]
    transaction_type: TransactionType
    concept_id: Optional[Union[uuid.UUID, str]] = None
    quantity_change: float = Field(..., description="Amount to add (positive) or remove (negative, handled by logic usually positive magnitude with OUT type)")
    weight: float = Field(0.0, description="Total weight of this item in movement")
    target_warehouse_id: Optional[Union[uuid.UUID, str]] = None
    unit_cost: Optional[float] = Field(0.0, description="Cost of the unit for CPP calculation (only for IN)")
    currency: str = Field("MXN", max_length=3)
    fulfill_reservation: bool = False
    reference_id: Optional[Union[uuid.UUID, str]] = None
    location: Optional[str] = None
    customs_pedimento_id: Optional[Union[uuid.UUID, str]] = None
    expiry_date: Optional[datetime] = None
    comments: Optional[str] = None

    @field_validator('uom_id', 'concept_id', 'target_warehouse_id', 'reference_id', 'location', 'customs_pedimento_id', mode='before')
    @classmethod
    def sanitize_optional_fields(cls, v):
        return _sanitize_uuid_field(v)



class DocumentLine(BaseModel):
    sku: str
    product_id: Union[uuid.UUID, str]
    quantity: float
    uom_id: Optional[Union[uuid.UUID, str]] = None
    weight: float
    unit_price: Decimal = Decimal("0.00")
    currency: str = "MXN"
    location: Optional[str] = None
    customs_pedimento_id: Optional[Union[uuid.UUID, str]] = None
    expiry_date: Optional[datetime] = None

    @field_validator('uom_id', 'customs_pedimento_id', mode='before')
    @classmethod
    def sanitize_uom_id(cls, v):
        return _sanitize_uuid_field(v)

class InventoryDocumentCreate(BaseModel):
    correlation_id: Union[uuid.UUID, str]
    type: TransactionType
    concept_id: Union[uuid.UUID, str]
    warehouse_id: Union[uuid.UUID, str]
    target_warehouse_id: Optional[Union[uuid.UUID, str]] = None
    external_entity: Optional[str] = None
    notes: Optional[str] = None
    items: list[DocumentLine]

class InventoryLevelRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    uom_id: uuid.UUID
    quantity: float
    reserved_quantity: float
    weighted_average_cost: float
    last_purchase_price: Decimal
    replacement_price: Decimal
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


class StockRelocationCreate(BaseModel):
    product_id: uuid.UUID
    uom_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: float
    from_location: str
    to_location: str
    concept_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    correlation_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)
