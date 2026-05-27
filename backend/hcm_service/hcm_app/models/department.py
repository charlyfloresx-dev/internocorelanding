import uuid
from typing import Optional
from sqlalchemy import String, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.infrastructure.models.base import MultiTenantBase

class Department(MultiTenantBase):
    """
    Department/Area organization entity in a multi-tenant manufacturing environment.
    Equivalent to legacy .NET Department + Area catalogs (merged).
    """
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_department_code_company"),
    )

    def __repr__(self) -> str:
        return f"<Department id={self.id} code={self.code} name={self.name}>"
