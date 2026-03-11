from typing import Optional, List
import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import MultiTenantBase

class User(MultiTenantBase):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email = Column(sa.String(255), unique=True, nullable=False)
    hashed_password = Column(sa.String(255), nullable=True)
    identity_token = Column(sa.String(255), nullable=True, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Sobrescribimos company_id para agregar ForeignKey explicitamente
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)

    # Relations
    company: Mapped[Optional["Company"]] = relationship("Company", foreign_keys=[company_id])
    
    user_company_roles: Mapped[List["UserCompanyRole"]] = relationship(
        "UserCompanyRole", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )