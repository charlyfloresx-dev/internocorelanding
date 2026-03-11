from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Text
from ..infrastructure.models.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Text, primary_key=True) # O UUID
    table_name = Column(String(100), nullable=True) # Optional for global events like LOGIN
    record_id = Column(String(100), nullable=True) # Optional for global events
    action = Column(String(50), nullable=False) # e.g. LOGIN_SUCCESS, COMPANY_SELECTED
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    # Context
    user_id = Column(String(100), nullable=True)
    company_id = Column(String(100), nullable=True)
    group_id = Column(String(100), nullable=True)
    
    # Metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    trace_id = Column(String(100), nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)