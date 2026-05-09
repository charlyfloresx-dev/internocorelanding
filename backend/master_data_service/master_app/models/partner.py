import uuid
from typing import Optional
from sqlalchemy import String, Boolean, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column
from common.models import MultiTenantBase
from common.enums import PartnerType

class Partner(MultiTenantBase):
    """
    Representa a un socio comercial (Cliente, Proveedor o Ambos).
    """
    __tablename__ = "partners"

    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    tax_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # RFC en MX
    type: Mapped[PartnerType] = mapped_column(
        Enum(PartnerType),
        default=PartnerType.BOTH,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    price_list_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Partner(code='{self.code}', name='{self.name}', type='{self.type}')>"
