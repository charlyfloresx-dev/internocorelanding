import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Enum, DateTime, func, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.models import MultiTenantBase

class AgreementType(str, enum.Enum):
    CONTRACT = "CONTRACT"           # B2B Specific Agreement
    DISCOUNT_LIST = "DISCOUNT_LIST" # Broad list with discount rules
    GLOBAL = "GLOBAL"               # Standard prices for the company

class PriceAgreement(MultiTenantBase):
    """
    PriceAgreement (Contrato/Acuerdo de Precios)
    Es la entidad raíz que agrupa precios específicos para un cliente o canal.
    """
    __tablename__ = "price_agreements"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    agreement_type: Mapped[AgreementType] = mapped_column(
        Enum(AgreementType, create_type=False), 
        default=AgreementType.GLOBAL, 
        nullable=False
    )
    
    # El cliente asociado (si es un contrato específico)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        index=True, 
        nullable=True
    )
    
    # Campo para compatibilidad con el frontend (lista maestra)
    external_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Vigencia
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", default=True)
    
    # Metadata para auditoría y workflow
    review_status: Mapped[str] = mapped_column(String(50), server_default="APPROVED", default="APPROVED")
