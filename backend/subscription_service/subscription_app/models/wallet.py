import uuid
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from common.models import AuditBase

class GuestWallet(AuditBase):
    __tablename__ = "guest_wallets"

    guest_session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    balance_cents: Mapped[int] = mapped_column(Integer, default=0)

class WalletTransaction(AuditBase):
    __tablename__ = "wallet_transactions"

    guest_wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guest_wallets.id"))
    amount_cents: Mapped[int] = mapped_column(Integer)
    transaction_type: Mapped[str] = mapped_column(String(50)) # e.g. "REWARD", "PURCHASE"
    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # ID of the photo or order
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
