from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Text
from common.models.base_models import Base # O tu Base común

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Text, primary_key=True) # O UUID
    table_name = Column(String(100), nullable=False)
    record_id = Column(String(100), nullable=False)
    action = Column(String(20), nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    user_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)