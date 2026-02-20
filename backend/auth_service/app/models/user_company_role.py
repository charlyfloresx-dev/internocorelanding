import uuid
from typing import List, Optional
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB  # <-- Importe específico para evitar errores de renderizado
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase 

class UserCompanyRole(MultiTenantBase):
    __tablename__ = "user_company_roles"

    # Definición de IDs con UUID para coherencia con el ADN de Interno Core
    # Marcamos como primary_key=True para asegurar la unicidad de la relación triple
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True, nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), primary_key=True, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), primary_key=True, nullable=False)
    
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)

    # Scopes para claims granulares (ej: ["inventory:admin", "catalog:read"])
    # Usamos JSONB para permitir búsquedas eficientes en el futuro
    scopes: Mapped[Optional[List[str]]] = mapped_column(JSONB, default=list, nullable=True)

    # Relaciones con carga selectin para optimizar el login (evita el problema N+1)
    user: Mapped["User"] = relationship("User", back_populates="user_company_roles", lazy="selectin")
    company: Mapped["Company"] = relationship("Company", back_populates="user_company_roles", lazy="selectin")
    role: Mapped["Role"] = relationship("Role", back_populates="user_company_roles", lazy="selectin")

    def __repr__(self) -> str:
        return f"<UserCompanyRole(user={self.user_id}, company={self.company_id}, role={self.role_id})>"