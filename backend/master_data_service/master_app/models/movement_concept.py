import enum
import uuid
from typing import Optional
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase

from common.models import BaseMovementConcept

class MovementConcept(BaseMovementConcept):
    __tablename__ = "movement_concepts"

    # Override tenant fields to be nullable for Global concepts
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    requires_external_entity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_target_warehouse: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    translation_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<MovementConcept(name='{self.name}', type='{self.type}')>"
