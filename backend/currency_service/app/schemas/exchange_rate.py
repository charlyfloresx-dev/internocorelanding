from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
import uuid

class RateRead(BaseModel):
    id: uuid.UUID
    base_currency: str
    target_currency: str
    rate: Decimal
    source: str
    is_suspicious: bool
    is_verified: bool
    captured_at: datetime
    captured_by: Optional[uuid.UUID]

    class Config:
        from_attributes = True

class RateManualUpdate(BaseModel):
    target_currency: str = Field(..., min_length=3, max_length=3)
    rate: Decimal
    base_currency: str = "USD"

class RateSummaryItem(BaseModel):
    currency: str
    current_stored_rate: Optional[float]
    new_external_rate: Optional[float]
    variation_percentage: float
    is_drastic: bool
    last_update: Optional[datetime]

class RateSummaryResponse(BaseModel):
    company_id: str
    base_currency: str
    timestamp: datetime
    rates: List[RateSummaryItem]
