import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("permissions.id"), primary_key=True)

    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="role_permissions")
