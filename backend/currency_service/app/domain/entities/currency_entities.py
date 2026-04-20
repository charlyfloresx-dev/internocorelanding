from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

@dataclass
class CurrencyRate:
    id: UUID
    company_id: UUID
    base_currency: str
    target_currency: str
    rate: Decimal
    source: str
    is_suspicious: bool
    is_verified: bool
    captured_at: datetime
    captured_by: Optional[UUID] = None
