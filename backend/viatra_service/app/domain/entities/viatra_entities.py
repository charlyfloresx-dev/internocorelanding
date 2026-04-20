from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

@dataclass
class TravelerGroup:
    id: UUID
    company_id: UUID
    name: str
    package_id: UUID
    leader_name: Optional[str] = None
    flight_number: Optional[str] = None
    status: str = "PENDING"
    grace_period_until: Optional[datetime] = None
    tenant_id: Optional[UUID] = None

@dataclass
class ItineraryItem:
    id: UUID
    company_id: UUID
    group_id: UUID
    package_id: UUID
    name: str
    item_type: str  # ACCOMMODATION, FLIGHT, ACTIVITY
    confirmation_number: Optional[str] = None
    check_in_date: Optional[datetime] = None
    check_out_date: Optional[datetime] = None
    status: str = "ACTIVE"
    tenant_id: Optional[UUID] = None

@dataclass
class PriceAlert:
    id: UUID
    company_id: UUID
    package_id: UUID
    group_id: UUID
    flight_number: str
    old_price: Decimal
    new_price: Decimal
    currency: str
    alert_type: str
    notes: str
    created_at: datetime
    created_by: UUID

@dataclass
class TravelPackage:
    id: UUID
    company_id: UUID
    name: str
    total_price: Decimal
    target_price: Optional[Decimal] = None
    status: str = "ACTIVE"

@dataclass
class PaymentHistory:
    id: UUID
    company_id: UUID
    stripe_payment_id: str
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
