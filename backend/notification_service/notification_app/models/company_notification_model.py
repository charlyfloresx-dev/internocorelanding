import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from common.infrastructure.models.base import Base

class CompanyNotificationConfig(Base):
    """
    Stores encrypted Twilio/WhatsApp credentials for each company.
    Supports the Bring Your Own Key (BYOK) strategy.
    """
    __tablename__ = "company_notification_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    provider = Column(String(50), default="twilio", nullable=False)
    
    # Credentials (should be encrypted at app level)
    account_sid = Column(String(255), nullable=False)
    auth_token = Column(String(255), nullable=False)
    
    sender_number = Column(String(100), nullable=False)
    display_name = Column(String(200), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<CompanyNotificationConfig(company_id={self.company_id}, provider={self.provider})>"
