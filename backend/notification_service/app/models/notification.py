from sqlalchemy import String, Text, Enum as sqlalchemy_Enum, Boolean, UUID as sqlalchemy_UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase, Base
import uuid
import enum
from typing import List, Optional
from datetime import datetime

class NotificationPriority(enum.Enum):
    CRITICAL = "CRITICAL" # L1: Escalate everywhere
    HIGH = "HIGH"         # L2: Email + In-App
    MEDIUM = "MEDIUM"     # L3: In-App default
    LOW = "LOW"           # L4: Audit

class NotificationChannel(enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"

class NotificationStatus(enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"

class Notification(MultiTenantBase):
    __tablename__ = "notifications"

    type: Mapped[str] = mapped_column(String(50), index=True) # e.g., TICKET_CREATED, STOCK_BREAK
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    
    priority: Mapped[NotificationPriority] = mapped_column(sqlalchemy_Enum(NotificationPriority))
    channel: Mapped[NotificationChannel] = mapped_column(sqlalchemy_Enum(NotificationChannel))
    status: Mapped[NotificationStatus] = mapped_column(sqlalchemy_Enum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Store dynamic metadata as JSON string
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    recipients: Mapped[List["NotificationRecipient"]] = relationship(
        "NotificationRecipient", back_populates="notification", cascade="all, delete-orphan"
    )

class NotificationRecipient(MultiTenantBase):
    __tablename__ = "notification_recipients"

    notification_id: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(sqlalchemy_UUID(as_uuid=True), index=True)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    notification: Mapped["Notification"] = relationship("Notification", back_populates="recipients")
