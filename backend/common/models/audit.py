import uuid
import enum
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB

# Asumiendo una Base declarativa común, si no, se crea aquí.
Base = declarative_base()

class ActionType(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correlation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True)
    
    # User & Request Context
    user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Action Details
    action: Mapped[ActionType] = mapped_column(SAEnum(ActionType, name="actiontype_enum", create_type=True), nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Data Snapshots (The "Immutable Ledger" part)
    old_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    new_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} table={self.table_name} record_id={self.record_id}>"