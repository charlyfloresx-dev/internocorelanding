from typing import Optional, List
import uuid
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Usamos MultiTenantBase para forzar el aislamiento por company_id (Revertido por petición del usuario)
from common.models import MultiTenantBase

class User(MultiTenantBase):
    __tablename__ = "users"
    
    # El email es único POR EMPRESA en el modelo siloed original
    email: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # FK explícita restaurada
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    
    # Relaciones
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="users")
    
    # Mantenemos las membresías de roles
    user_company_roles: Mapped[List["UserCompanyRole"]] = relationship(
        "UserCompanyRole", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Volvemos a la unicidad por email + compañía
        UniqueConstraint("email", "company_id", name="uq_user_email_company"),
    )