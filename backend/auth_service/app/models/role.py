import uuid
from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

# --- ENTIDAD ROLE ---
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

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
        return f"<Role(name={self.name})>"