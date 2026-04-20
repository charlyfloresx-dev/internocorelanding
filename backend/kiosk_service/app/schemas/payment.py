import uuid
from typing import Optional
from pydantic import BaseModel
from app.domain.enums import PaymentMethod, PaymentStatus


# ─── Request Schemas ───────────────────────────────────────────────────────────

class CreatePaymentIn(BaseModel):
    """Guest initiates payment for one or more photos."""
    event_id: uuid.UUID
    company_id: uuid.UUID
    guest_session_id: str
    photo_ids: list[uuid.UUID]
    method: PaymentMethod   # STRIPE | CASH
    use_wallet_balance: Optional[bool] = False


class ConfirmCashPaymentIn(BaseModel):
    """Staff tablet scans QR token to mark order as COMPLETED."""
    cash_qr_token: str


# ─── Response Schemas ──────────────────────────────────────────────────────────

class PaymentOrderOut(BaseModel):
    id: uuid.UUID
    photo_id: uuid.UUID
    amount_cents: int
    currency: str
    method: PaymentMethod
    status: PaymentStatus
    # Stripe flow
    stripe_client_secret: Optional[str] = None
    # Cash flow
    cash_qr_token: Optional[str] = None
    qr_image_url: Optional[str] = None   # base64 PNG embedded in response

    class Config:
        from_attributes = True
