import uuid
import enum
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from common.infrastructure.models.base import MultiTenantBase


class ActionType(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditLog(MultiTenantBase):
    """
    Inmutable Ledger de auditoría multi-tenant.
    Cada registro de auditoría queda vinculado a un tenant/company para trazabilidad completa.
    """
    __tablename__ = 'audit_logs'

    correlation_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True)
    
    # Multitenancy (Overrides MultiTenantBase to be optional for Audit)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # User & Identity Context (Triple Identidad)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), index=True) # Identidad Digital
    collaborator_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True) # Identidad Física
    external_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True) # Identidad Externa
    
    client_ip: Mapped[Optional[str]] = mapped_column(String(50))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))

    # Action Details
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    table_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    record_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Data Snapshots (The "Immutable Ledger" part)
    old_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    new_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    # Timestamp (alias over inherited created_at for backwards compatibility)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} table={self.table_name} record_id={self.record_id}>"