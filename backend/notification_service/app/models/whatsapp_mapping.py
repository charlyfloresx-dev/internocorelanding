"""
WhatsApp Group Mapping Model
─────────────────────────────
Maps internal company groups (by role/function name) to external WhatsApp Group IDs.
Enforces multitenancy isolation: each company has its own set of mappings.

The whatsapp_group_id follows the format used by providers (e.g., "123456789@g.us"
for WhatsApp native, or a provider-specific ID for Twilio/MessageBird).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from common.infrastructure.models.base import Base


class WhatsAppGroupMapping(Base):
    __tablename__ = "whatsapp_group_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), index=True, nullable=False)

    # Nombre lógico del grupo interno (e.g., "TECNICOS_PLANTA", "SUPERVISORES", "ADMIN")
    group_name = Column(String(100), nullable=False, index=True)

    # ID externo del grupo de WhatsApp (formato 123456789@g.us o ID del proveedor)
    whatsapp_group_id = Column(String(255), nullable=False)

    # Nombre legible para UI / auditoría
    display_name = Column(String(200), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "group_name": self.group_name,
            "whatsapp_group_id": self.whatsapp_group_id,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
