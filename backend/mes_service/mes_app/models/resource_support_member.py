import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.infrastructure.models.base import MultiTenantBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .resource import Resource


class ResourceSupportMember(MultiTenantBase):
    """
    Equipo de soporte asignado a un recurso de producción.
    collaborator_id es soft FK hacia hcm_service.collaborators (Iron Wall — sin FK de BD).
    """
    __tablename__ = "mes_resource_support_members"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("mes_resources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Soft FK → hcm_service.collaborators.id
    collaborator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    resource: Mapped["Resource"] = relationship("Resource", back_populates="support_members")
