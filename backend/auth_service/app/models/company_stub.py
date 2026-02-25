import uuid
from typing import Optional, List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)