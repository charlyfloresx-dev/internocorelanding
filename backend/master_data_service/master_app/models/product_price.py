"""
ProductPrice — Modelo de Lista de Precios Multi-Tenant (Phase 33.5)
====================================================================
Soporte para 10 listas de precios configurables por empresa:
  - Lista 1 (General/Público), Lista 2 (Mayoreo), ..., Lista 10 (Empleado)
  - Precios siempre netos (sin impuestos). IVA/Sales Tax se calculan al checkout.
  - Diferenciación por unidad: BASE (caja, pallet) vs SALE (pieza, ml).
  - allow_price_override en Product determina si el usuario puede editar en transacción.

Alineado con:
  - Requerimiento de Areli: "le pongo el precio que yo quiera" en el movimiento.
  - Arquitectura Zero-Trust: company_id obligatorio vía MultiTenantBase.
  - Compatibilidad transfronteriza: MXN para México, USD para EE. UU.
"""

import uuid
from sqlalchemy import String, Integer, Boolean, Numeric, ForeignKey, UniqueConstraint, Enum as SAEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
import enum

from common.models import MultiTenantBase

if TYPE_CHECKING:
    from master_app.models.product import Product


class UnitType(str, enum.Enum):
    """Diferencia el precio en Unidad Base (ej. Caja) vs Unidad de Venta (ej. Pieza)."""
    BASE = "BASE"
    SALE = "SALE"


class ProductPrice(MultiTenantBase):
    """
    Tabla de precios del catálogo maestro.

    La jerarquía de resolución de precios es:
      1. Almacén específico (warehouse_id NOT NULL) — precio de logística local.
      2. Empresa global (warehouse_id NULL) — precio base para todo el tenant.

    El precio en una transacción siempre puede ser sobrescrito si
    Product.allow_price_override == True (ver Modo Areli).
    """
    __tablename__ = "product_prices"

    # ── Relación con el producto ─────────────────────────────────────────────
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product: Mapped["Product"] = relationship("Product", back_populates="prices")

    # ── Lista de Precios (1-10) ──────────────────────────────────────────────
    # 1 = General/Público, 2 = Mayoreo, 3 = Distribuidores, ... 10 = Empleado
    price_list_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        # CHECK constraint definido en __table_args__
    )

    # ── Precio neto (sin impuestos) ──────────────────────────────────────────
    # El IVA / Sales Tax se aplica al final del documento según is_taxable del Product.
    # Columnas mapeadas por composite 'price'
    _amount: Mapped[Decimal] = mapped_column("amount", Numeric(12, 4), nullable=False)
    _currency: Mapped[str] = mapped_column("currency", String(3), nullable=False, default="MXN")

    from sqlalchemy.orm import composite
    from common.value_objects import Money
    price: Mapped[Money] = composite(Money, _amount, _currency)

    @property
    def amount(self) -> Decimal:
        return self._amount

    @amount.setter
    def amount(self, value: Decimal):
        self._amount = value

    @property
    def currency(self) -> str:
        return self._currency

    @currency.setter
    def currency(self, value: str):
        self._currency = value

    # ── Unidad de medida del precio ─────────────────────────────────────────
    unit_type: Mapped[UnitType] = mapped_column(
        SAEnum(UnitType, name="product_price_unit_type", create_type=True),
        nullable=False,
        default=UnitType.SALE
    )

    # ── Almacén específico (opcional) ────────────────────────────────────────
    # Si es NULL → precio aplica a toda la empresa (Global).
    # Si tiene valor → precio específico para ese almacén (ej: Tijuana vs Otay).
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    # ── Vigencia ─────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Soft-Close (Inmutabilidad de Precios) ────────────────────────────────
    # NULL = precio vigente. Con valor = precio histórico cerrado en esa fecha.
    # Al actualizar un precio: se sella valid_until del registro anterior
    # y se crea un nuevo registro con valid_until = NULL.
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    # ── Auditoría de Override Manual ─────────────────────────────────────────
    # True si el operador sobrescribió manualmente el tabulador en una transacción.
    # False = precio oficial de las listas 1-10.
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        # Un producto sólo puede tener UN precio activo por lista + unidad + almacén + moneda.
        UniqueConstraint(
            "company_id", "product_id", "price_list_index",
            "unit_type", "warehouse_id", "currency",
            name="_product_price_unique_uc"
        ),
        # Índice compuesto para lookups de resolución de precio O(log n).
        # Búsqueda típica: "Dame el precio de MAT-001 en lista 1, moneda MXN para esta empresa".
        # {"schema": ..., "index_composition": ["company_id", "product_id", "price_list_index", "is_active"]},
    )
