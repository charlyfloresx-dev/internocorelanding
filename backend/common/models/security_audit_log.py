import uuid
from typing import Optional, Any
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from common.infrastructure.models.base import AuditBase

class SecurityAuditLog(AuditBase):
    __tablename__ = "security_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Referencia cruzada
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    collaborator_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Trazabilidad de acceso
    access_method: Mapped[str] = mapped_column(String(50)) # 'WEB_FORM', 'PIN_PAD', 'RFID_SCAN'
    identity_identifier: Mapped[str] = mapped_column(String(255)) # Correo, PIN o ID de Tag (ofuscado si es PIN)
    
    # El "Snapshot" de los roles calculados al vuelo
    roles_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON) # Ej: ["collaborator", "warehouse_manager"]
    scopes_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON) # Ej: ["inv:movements:manage"]
    
    # Contexto físico
    terminal_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # ID de la tablet o PC en planta
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50)) # 'SUCCESS', 'FAILED_AUTH', 'REVOKED'

    def __repr__(self):
        return f"<SecurityAuditLog id={self.id} method={self.access_method} status={self.status}>"
