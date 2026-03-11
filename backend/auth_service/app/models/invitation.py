import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models import MultiTenantBase

class Invitation(MultiTenantBase):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=7))
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Sobrescribimos company_id para agregar ForeignKey explicitamente
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)

    # Relaciones
    company: Mapped["Company"] = relationship("Company", foreign_keys=[company_id])
    role: Mapped["Role"] = relationship("Role")

    def __repr__(self) -> str:
        return f"<Invitation(email={self.email}, code={self.code}, used={self.is_used})>"
