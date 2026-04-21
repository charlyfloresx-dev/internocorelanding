import uuid
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase

# --- ENTIDAD ROLE ---
class Role(MultiTenantBase):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    is_system_role: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    # Sobrescribimos company_id para que sea nullable (Roles Maestros / Globales)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(sa.UUID(as_uuid=True), nullable=True, index=True)

    __table_args__ = (
        sa.UniqueConstraint("name", "company_id", name="uq_role_name_company"),
    )

    # Relación muchos a muchos a través de la clase RolePermission
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", 
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Relación uno a muchos con UserCompanyRole (Identidad Triple)
    user_company_roles: Mapped[List["UserCompanyRole"]] = relationship("UserCompanyRole", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(name={self.name}, is_system={self.is_system_role})>"
