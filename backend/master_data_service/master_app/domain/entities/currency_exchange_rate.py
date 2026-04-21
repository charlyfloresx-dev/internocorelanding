import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass

@dataclass
class CurrencyExchangeRateEntity:
    company_id: uuid.UUID
    base_currency: str
    target_currency: str
    rate: Decimal
    is_suspicious: bool = False
    is_verified: bool = False
    captured_at: Optional[datetime] = None
    captured_by: Optional[uuid.UUID] = None
    id: Optional[uuid.UUID] = None
