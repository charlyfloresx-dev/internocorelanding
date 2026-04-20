import uuid
from sqlalchemy import String, Column
from common.infrastructure.models.base import Base

class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    
    key = Column(String(255), primary_key=True)
