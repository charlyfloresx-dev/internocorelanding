import uuid
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase

class Permission(MultiTenantBase):

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(100), unique=True, nullable=False)
    module_name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)

    # Sobrescribimos company_id para que sea nullable (Permisos Globales)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)

    __table_args__ = (
        sa.UniqueConstraint("name", "company_id", name="uq_permission_name_company"),
    )

    # Relación muchos a muchos con roles
    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="permission")