from typing import Optional, List
import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Usamos MultiTenantBase para forzar el aislamiento por company_id (Revertido por petición del usuario)
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email = Column(sa.String(255), unique=True, nullable=False)
    hashed_password = Column(sa.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # FK explícita restaurada
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False, index=True)
    
    # Relaciones
    company: Mapped[Optional["Company"]] = relationship("Company")
    
    # Mantenemos las membresías de roles
    user_company_roles: Mapped[List["UserCompanyRole"]] = relationship(
        "UserCompanyRole", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )