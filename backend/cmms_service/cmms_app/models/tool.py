"""
Tool — Herramienta del Tool Crib (activo circulante con QR HMAC).

DISEÑO: Este modelo es una CAPA DE METADATA DE MANTENIMIENTO sobre el
Inventory Service. Nunca duplica el catálogo de ítems.
- inventory_item_id: Referencia débil (UUID) al InventoryItem del WMS.
  El nombre/marca/modelo se denormalizan aquí solo como caché de lectura rápida;
  la fuente de verdad es el Inventory Service.
- Para Check-out: CMMS envía un InventoryTransaction(type=INTERNAL_LOAN)
  al Inventory Service → cambia status a LENT y actualiza ubicación al
  WorkOrder ID / Technician ID.
- Para consumibles (lubricante, tornillos, etc.): CMMS dispara un
  InventoryTransaction(type=PICK_AND_CONSUME) — baja definitiva sin retorno.
"""
import uuid
import hmac
import hashlib
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, DateTime, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import MultiTenantBase
from cmms_app.core.constants import ToolStatus, ToolCondition

if TYPE_CHECKING:
    from .tool_assignment import ToolAssignment


class Tool(MultiTenantBase):
    """
    Herramienta de inventario (activo circulante).
    Puede prestarse entre técnicos vinculada a una WorkOrder.
    El sistema bloquea el préstamo si el estado no es AVAILABLE.
    """
    __tablename__ = "cmms_tools"

    # ── Referencia al Inventory Service (fuente de verdad) ─────────────────────
    # Weak-ref: no FK cross-service. El Inventory Service es el maestro de ítems.
    inventory_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    internal_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)  # caché — fuente de verdad en Inventory
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(150), unique=True, nullable=True)

    # ── Estado y ubicación ───────────────────────────────────────────────────
    status: Mapped[ToolStatus] = mapped_column(SAEnum(ToolStatus), default=ToolStatus.AVAILABLE, nullable=False, index=True)
    condition: Mapped[ToolCondition] = mapped_column(SAEnum(ToolCondition), default=ToolCondition.GOOD, nullable=False)
    current_warehouse_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # ── Calibración ──────────────────────────────────────────────────────────
    is_calibratable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_calibration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_calibration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    calibration_certificate: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── QR Identity (HMAC-signed) ─────────────────────────────────────────────
    qr_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    assignments: Mapped[List["ToolAssignment"]] = relationship("ToolAssignment", back_populates="tool", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cmms_tools_company_status", "company_id", "status"),
        Index("ix_cmms_tools_company_warehouse", "company_id", "current_warehouse_id"),
        Index("ix_cmms_tools_company_code", "company_id", "internal_code", unique=True),
    )

    def generate_qr_token(self, secret: str) -> str:
        payload = f"v1/tools/{self.id}"
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        self.qr_token = sig
        return f"{payload}?sig={sig}"
