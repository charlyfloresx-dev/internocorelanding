import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..infrastructure.models.base import AuditBase

class BusinessGroup(AuditBase):
    __tablename__ = "business_groups"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Companies in this business group
    companies: Mapped[list["Company"]] = relationship(
        "Company", 
        back_populates="business_group",
        foreign_keys="Company.parent_group_id"
    )

    def __repr__(self) -> str:
        return f"<BusinessGroup(name={self.name})>"
