import uuid
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class UserCompanyRole(Base):
    __tablename__ = "user_company_roles"

    # Definición de IDs con UUID para coherencia con el ADN de Interno Core
    # Marcamos como primary_key=True para asegurar la unicidad de la relación triple
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True, nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), primary_key=True, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), primary_key=True, nullable=False)
    
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)

    # Scopes para claims granulares (ej: ["inventory:admin", "catalog:read"])
    # Usamos JSONB para permitir búsquedas eficientes en el futuro
    scopes = Column(postgresql.JSONB, server_default=sa.text("'[]'::jsonb"), nullable=True)

    # Relaciones con carga selectin para optimizar el login (evita el problema N+1)
    user: Mapped["User"] = relationship("User", back_populates="user_company_roles", lazy="selectin")
    company: Mapped["Company"] = relationship("Company", lazy="selectin")
    role: Mapped["Role"] = relationship("Role", back_populates="user_company_roles", lazy="selectin")

    def __repr__(self) -> str:
        return f"<UserCompanyRole(user={self.user_id}, company={self.company_id}, role={self.role_id})>"