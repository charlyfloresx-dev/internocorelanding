import uuid
from sqlalchemy import Column, ForeignKey, Table, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING

from common.infrastructure.models.base import MultiTenantBase, Base

# Tabla asociativa para la relación N:N con Partners (Proveedores)
# Se usa UUID explícito para compatibilidad industrial y evitar ambigüedad en el Monolito
partner_contacts = Table(
    "partner_contacts",
    Base.metadata,
    Column("partner_id", UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), primary_key=True),
    Column("external_contact_id", UUID(as_uuid=True), ForeignKey("external_contacts.id", ondelete="CASCADE"), primary_key=True)
)

class ExternalContact(MultiTenantBase):
    """
    Gestor o técnico de un Partner/Proveedor (Fusión de Contact.cs y Person.cs).
    No consume licencias internas (Zero-Consumption).
    """
    __tablename__ = "external_contacts"

    # Identidad
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Rol Operativo
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relación N:N conceptual (Se puede completar si se importa Partner en el servicio)
    # providers: Mapped[List["Partner"]] = relationship("Partner", secondary=partner_contacts, back_populates="contacts")
