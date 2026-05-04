"""
Enumeration — Tabla centralizada para manejar enums dinámicos, traducciones y personalización por tenant.
"""
import uuid
from typing import Optional

from sqlalchemy import String, Boolean, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.infrastructure.models.base import MultiTenantBase


class Enumeration(MultiTenantBase):
    """
    Tabla centralizada para manejar enums dinámicos, 
    traducciones y personalización por tenant.
    """
    __tablename__ = 'enumerations'

    # Override company_id para registros globales (SaaS core)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # 'type' define el grupo (ej: 'ASSET_CATEGORY', 'WORK_ORDER_STATUS')
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 'key' es el valor que se guarda en la DB (ej: 'MACHINERY', 'LOW')
    key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # 'label' es el valor por defecto legible (en inglés o español base)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 'translation_key' para i18n (ej: 'enums.asset_category.machinery')
    translation_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Orden de visualización en selectores
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Permite desactivar opciones sin borrarlas
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('type', 'key', 'company_id', name='uq_enum_type_key_company'),
        Index('ix_enumerations_type_company_active', 'type', 'company_id', 'is_active'),
    )
