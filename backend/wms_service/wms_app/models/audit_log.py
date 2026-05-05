import uuid
from typing import Optional, Any
from sqlalchemy import String, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase

class AuditLog(MultiTenantBase):
    """
    Registro de auditoría para eventos de negocio y excepciones en WMS.
    """
    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Contexto opcional capturado del request_context
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    trace_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Referencia opcional a un recurso relacionado (ej. product_id, order_id)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
