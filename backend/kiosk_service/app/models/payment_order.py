import uuid
from sqlalchemy import String, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import AuditBase
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.event_photo import EventPhoto


from app.domain.enums import PaymentMethod, PaymentStatus


class PaymentOrder(AuditBase):
    __tablename__ = "payment_orders"

    photo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("event_photos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    guest_session_id: Mapped[str] = mapped_column(String(128), nullable=False)

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)   # e.g. 5000 = $50 MXN
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MXN")

    method: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method"), nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )

    # Stripe specific (null for cash orders)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    stripe_client_secret: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Cash specific — QR token the staff scans
    cash_qr_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)

    # Relationship
    photo: Mapped["EventPhoto"] = relationship("EventPhoto", back_populates="payment_orders")
