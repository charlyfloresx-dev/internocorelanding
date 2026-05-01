import uuid
from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field
from mes_app.core.enums import ProductionEventType

class BaseSchema(BaseModel):
    """
    Base schema including Audit fields in a serializable way.
    """
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    transaction_id: Optional[uuid.UUID] = None

class EventMetaData(BaseModel):
    client_timestamp: datetime
    device_id: Optional[str] = None

class ProductionEventBase(BaseSchema):
    resource_id: uuid.UUID
    order_id: uuid.UUID
    event_type: ProductionEventType
    quantity: Decimal = Field(default=0)
    reason_code: Optional[str] = None
    meta_data: Optional[EventMetaData] = None

class RegisterProductionEventCommand(ProductionEventBase):
    event_id: uuid.UUID # Client generated UUID for idempotency
    company_id: Optional[uuid.UUID] = None # Auto-injected from context

class ProductionEventResponse(ProductionEventBase):
    id: uuid.UUID
    company_id: uuid.UUID
    
    class Config:
        from_attributes = True
