"""MaintenanceEvidence — Archivo de evidencia (foto/PDF) adjunto a una WorkOrder."""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models import MultiTenantBase

if TYPE_CHECKING:
    from .work_order import MaintenanceWorkOrder


class MaintenanceEvidence(MultiTenantBase):
    """
    Archivo de evidencia (foto 'antes/después', PDF de servicio) adjunto a una WorkOrder.
    El campo file_size_bytes es crítico: se usa para actualizar la StorageQuota del tenant
    en tiempo real al subir/eliminar archivos.
    """
    __tablename__ = "cmms_maintenance_evidence"

    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cmms_work_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Identificación del archivo ────────────────────────────────────────────
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)           # S3 key o ruta local
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)  # Para cuota de almacenamiento
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_thumbnail: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Metadata ─────────────────────────────────────────────────────────────
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    work_order: Mapped["MaintenanceWorkOrder"] = relationship("MaintenanceWorkOrder", back_populates="evidence_files")

    __table_args__ = (
        Index("ix_cmms_evidence_company_wo", "company_id", "work_order_id"),
    )
