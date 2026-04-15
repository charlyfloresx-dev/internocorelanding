import uuid
import enum
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Numeric, Enum, DateTime, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from common.models import MultiTenantBase

class DocumentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSED = "PROCESSED"
    CANCELLED = "CANCELLED"

class InventoryDocument(MultiTenantBase):
    __tablename__ = "inventory_documents"

    folio: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    document_type: Mapped[str] = mapped_column(String(20), nullable=False) # ENTRY, EXIT, TRANSFER, ICT_OUT, ICT_IN
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), server_default="DRAFT", default=DocumentStatus.DRAFT)
    
    # Names for direct UI representation (Industrial Mimesis)
    origin_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    destination_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Aggregates for quick listing
    total_items: Mapped[int] = mapped_column(default=0)
    total_weight: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0"))
    
    # Financial aggregate
    total_amount_val: Mapped[Decimal] = mapped_column("total_amount", Numeric(18, 4), default=Decimal("0.0"))
    total_currency: Mapped[str] = mapped_column("total_currency", String(3), default="USD")
    
    from sqlalchemy.orm import composite
    from common.domain.value_objects import Money
    total_amount: Mapped[Money] = composite(Money, total_amount_val, total_currency)
    
    concept_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, nullable=True)
    external_reference: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # ── Compliance: Sello de Agua Fiscal ──────────────────────────────────────
    # Si True: el documento fue creado sin precio pactado. Aparecerá en el
    # widget de "Pendientes de Valoración" del módulo de Finanzas.
    # INDEXED para que la query del widget sea eficiente en producción AWS.
    pending_financial_valuation: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
        comment="True cuando el movimiento se creó sin precio pactado. Requiere regularización en Finanzas."
    )

    # Notas de auditoría de compliance (JSON serializado como texto)
    audit_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON con warnings y metadatos del Agente de Auditoría Pre-Vuelo."
    )

    def __repr__(self):
        return f"<InventoryDocument(folio={self.folio}, type={self.document_type}, status={self.status}, pending_valuation={self.pending_financial_valuation})>"
