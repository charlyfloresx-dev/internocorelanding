"""
PriceAgreement — Contrato B2B Inmutable (Phase 34)
====================================================
Implementa el patron "Soft Close & Insert":
  - El campo 'valid_until' es NULL cuando el acuerdo esta activo.
  - Para actualizar un precio: se sella valid_until del registro vigente
    con func.now() y se inserta una NUEVA FILA con el nuevo monto.
  - NUNCA se modifica el campo 'amount' de un registro existente.

Consulta "Point-in-Time":
  SELECT * FROM price_agreements
  WHERE product_id = X AND partner_id = Y AND currency = Z
    AND valid_from <= :fecha AND (valid_until IS NULL OR valid_until > :fecha)
"""
import uuid
from sqlalchemy import String, Boolean, Numeric, ForeignKey, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal

from common.models import MultiTenantBase

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.partner import Partner


class PriceAgreement(MultiTenantBase):
    """
    Cada fila representa UNA VERSION INMUTABLE de un precio acordado
    entre la empresa (tenant) y un socio comercial (partner).

    La version activa siempre tiene valid_until = NULL.
    Las versiones historicas tienen valid_until con timestamp de cierre.
    """
    __tablename__ = "price_agreements"

    # -- Entidades Relacionadas -----------------------------------------------
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product: Mapped["Product"] = relationship("Product")

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    partner: Mapped["Partner"] = relationship("Partner")

    # -- Valoracion Inmutable --------------------------------------------------
    # Estos campos NUNCA se actualizan. Para cambiarlos, se crea nueva version.
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MXN")

    # -- Bitacora de Vigencia (Soft-Close Engine) ------------------------------
    # valid_from: fecha de inicio de este precio. Default = ahora.
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )
    # valid_until: NULL = precio vigente. Con valor = precio historico.
    # NUNCA se asigna en INSERT. Solo se actualiza en el Soft-Close.
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # -- Referencia Legal y Trazabilidad ---------------------------------------
    document_reference: Mapped[Optional[str]] = mapped_column(
        String(250), nullable=True,
        comment="Folio o UUID S3 del contrato fisico escaneado"
    )
    # Origen del dato: 'MANUAL' (desde UI) o 'CSV_IMPORT' (carga masiva).
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="MANUAL")
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # -- SIN UniqueConstraint --------------------------------------------------
    # La unicidad del registro ACTIVO se garantiza a nivel aplicacion:
    # solo un registro con valid_until=NULL por (product_id, partner_id, currency).
    # La BD almacena multiples versiones historicas del mismo binomio.
    __table_args__ = ()
