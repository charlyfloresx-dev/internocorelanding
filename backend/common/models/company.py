from typing import Optional, List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base_models import AuditBase

class Company(AuditBase):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # AÑADIR ESTA LÍNEA:
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) 
    
    # Relaciones (que ya arreglamos)
    users: Mapped[List["User"]] = relationship("User", back_populates="company")
    user_company_roles: Mapped[List["UserCompanyRole"]] = relationship("UserCompanyRole", back_populates="company")