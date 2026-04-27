import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
from common.infrastructure.models.base import Base

class NotificationPriority(str, Enum):
    CRITICAL = "CRITICAL" # L1: Escalate everywhere
    HIGH = "HIGH"         # L2: Email + In-App
    MEDIUM = "MEDIUM"     # L3: In-App default
    LOW = "LOW"           # L4: Audit

class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"

class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    DELIVERED = "DELIVERED"

class NotificationCategory(str, Enum):
    INFO = "INFO"
    INVENTORY = "INVENTORY"
    COMPLIANCE = "COMPLIANCE"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    type = Column(String(50), index=True) # e.g., TICKET_CREATED, STOCK_BREAK
    category = Column(SQLEnum(NotificationCategory), default=NotificationCategory.INFO)
    event_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.MEDIUM)
    channel = Column(SQLEnum(NotificationChannel), default=NotificationChannel.IN_APP)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Contexto persistente (JSON es mejor que String Text para industrial)
    payload = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    recipients = relationship("NotificationRecipient", back_populates="notification", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "payload": self.payload
        }

class NotificationRecipient(Base):
    __tablename__ = "notification_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    notification_id = Column(UUID(as_uuid=True), ForeignKey("notifications.id", ondelete="CASCADE"), index=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    notification = relationship("Notification", back_populates="recipients")
