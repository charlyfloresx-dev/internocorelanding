import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


class SubscriptionStatus(str, Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"


class PlanEntity(BaseModel):
    """Pure domain entity for a Subscription Plan (Product in Stripe)."""
    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    stripe_product_id: str
    is_active: bool = True


class PriceEntity(BaseModel):
    """Pure domain entity for a Plan Price."""
    id: uuid.UUID
    plan_id: uuid.UUID
    stripe_price_id: str
    amount: float
    currency: str
    interval: str  # month, year
    is_active: bool = True


class SubscriptionEntity(BaseModel):
    """Pure domain entity for a Customer Subscription."""
    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: str  # Stripe Customer ID
    stripe_subscription_id: str
    status: SubscriptionStatus
    plan_id: uuid.UUID
    current_period_end: datetime
    cancel_at_period_end: bool = False


class EntitlementEntity(BaseModel):
    """Pure domain entity for a Module/Feature Permission."""
    id: uuid.UUID
    company_id: uuid.UUID
    module_name: str
    is_enabled: bool = True
