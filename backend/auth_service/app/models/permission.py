from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Solo importamos BaseEntity (que ya trae a Base)
from common.models import BaseEntity

class Permission(BaseEntity): # <-- Limpiamos la herencia aquí
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relación muchos a muchos con roles
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", 
        back_populates="permission"
    )