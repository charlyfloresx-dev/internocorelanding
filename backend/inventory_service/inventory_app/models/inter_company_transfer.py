"""
InterCompanyTransfer — ORM Model
=====================================
Representa el documento de tránsito que actúa como intermediario confiable
(Trusted Broker) entre dos empresas en una transferencia de inventario.
"""

import uuid
import enum
from typing import Optional
from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, Numeric, Enum as SAEnum, Text, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, composite
from common.models import MultiTenantBase
from common.domain.value_objects import Money


class TransferStatus(str, enum.Enum):
    """Estados del documento de transferencia inter-company."""
    PENDING   = "PENDING"     # Creado, reserva activa en Empresa A
    SHIPPED   = "SHIPPED"     # Stock en tránsito, Empresa B puede "ver la carga"
    DELIVERED = "DELIVERED"   # Empresa B confirmó recepción
    CANCELLED = "CANCELLED"   # Cancelado antes de ser recibido


class InterCompanyTransfer(MultiTenantBase):
    """
    Documento de Tránsito Inter-Company.
    """
    __tablename__ = "inter_company_transfers"

    folio: Mapped[str] = mapped_column(
        String(60), unique=True, index=True, nullable=False,
        comment="Número de folio único: ICT-{YYYYMMDD}-{SHORT_UUID}"
    )

    # ── Partes Involucradas ────────────────────────────────────────────────────
    destination_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID, nullable=False, index=True,
        comment="UUID de la empresa DESTINO (Empresa B)"
    )

    origin_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    destination_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    transit_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)

    product_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False, index=True)
    uom_id: Mapped[uuid.UUID] = mapped_column(UUID, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0"))

    # ── Finanzas Cross-Company ────────────────────────────────────────────────
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    _unit_price_at_dispatch: Mapped[Decimal] = mapped_column(
        "unit_price_at_dispatch", Numeric(18, 4), nullable=True, default=Decimal("0.0")
    )
    _wac_at_dispatch: Mapped[Optional[Decimal]] = mapped_column(
        "wac_at_dispatch", Numeric(18, 4), nullable=True, default=Decimal("0.0")
    )
    _transfer_revenue_a: Mapped[Optional[Decimal]] = mapped_column(
        "transfer_revenue_a", Numeric(18, 4), nullable=True, default=Decimal("0.0")
    )
    _acquisition_cost_b: Mapped[Optional[Decimal]] = mapped_column(
        "acquisition_cost_b", Numeric(18, 4), nullable=True, default=Decimal("0.0")
    )

    unit_price: Mapped[Money] = composite(Money, _unit_price_at_dispatch, currency)
    wac_origin: Mapped[Optional[Money]] = composite(Money, _wac_at_dispatch, currency)
    revenue_a: Mapped[Optional[Money]] = composite(Money, _transfer_revenue_a, currency)
    cost_b: Mapped[Optional[Money]] = composite(Money, _acquisition_cost_b, currency)

    status: Mapped[TransferStatus] = mapped_column(
        SAEnum(TransferStatus, name="transfer_status_enum", native_enum=False),
        nullable=False, default=TransferStatus.PENDING, server_default="PENDING", index=True
    )

    # ── Compliance (Phase 40) ──────────────────────────────────────────────
    customs_pedimento: Mapped[Optional[str]] = mapped_column(String(21), nullable=True, index=True)
    customs_pedimento_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True, index=True)
    customs_doc_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    pending_financial_valuation: Mapped[bool] = mapped_column(nullable=False, default=False, index=True)
    audit_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exchange_rate_dof: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)

    # ── Metadatos ─────────────────────────────────────────────────────────────
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    received_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)
    received_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    damaged_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True, default=Decimal("0.0"))

    mirror_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True, index=True)
    inbound_folio: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    origin_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    destination_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    destination_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    receive_movement_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)
    dispatch_movement_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)

    def __repr__(self):
        return f"<InterCompanyTransfer(folio={self.folio}, status={self.status}, qty={self.quantity})>"
