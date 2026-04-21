import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from inventory_app.domain.entities.customs import CustomsOperationType

class CustomsPedimentoBase(BaseModel):
    pedimento_number: str = Field(..., min_length=15, max_length=15, description="15-digit Mexican Pedimento number")
    customs_key: str = Field(..., description="e.g., IN, AF, RT, V1")
    operation_type: CustomsOperationType
    customs_date: datetime
    is_temporary: bool = False
    exchange_rate_dof: Optional[float] = None
    comments: Optional[str] = None

class CustomsPedimentoCreate(CustomsPedimentoBase):
    pass

class CustomsPedimentoRead(CustomsPedimentoBase):
    id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class CustomsBalanceSchema(BaseModel):
    """Schema for Anexo 24 Compliance Balance Report line items."""
    item_id: uuid.UUID
    sku: Optional[str] = None
    product_name: Optional[str] = None
    customs_pedimento_id: Optional[uuid.UUID] = None
    pedimento_number: Optional[str] = None
    total_available_qty: Decimal
    expiry_date: Optional[datetime] = None
    days_to_expiry: Optional[int] = None
    is_at_risk: bool = False # Alert if < 30 days

class CustomsBalanceReportResponse(BaseModel):
    status: str = "success"
    data: list[CustomsBalanceSchema]
    total_count: int
    metadata: dict = {}
