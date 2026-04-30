from typing import Optional, List
import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import BaseEntity

class User(BaseEntity):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Identity
    first_name = Column(sa.String(100), nullable=True)
    last_name_pat = Column(sa.String(100), nullable=True)
    last_name_mat = Column(sa.String(100), nullable=True)
    
    # Compliance & Cross-Border
    rfc = Column(sa.String(50), nullable=True, index=True)
    curp = Column(sa.String(50), nullable=True, index=True)
    visa_number = Column(sa.String(50), nullable=True)
    sentry_id = Column(sa.String(50), nullable=True)
    
    # Auth Control
    is_biometric_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relations
    credentials: Mapped[List["UserCredential"]] = relationship(
        "UserCredential", back_populates="user", cascade="all, delete-orphan"
    )
    user_company_roles: Mapped[List["UserCompanyRole"]] = relationship(
        "UserCompanyRole", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )
