from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import String, Boolean, Integer, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from common.infrastructure.models.base import MultiTenantBase


class CollaboratorBadge(MultiTenantBase):
    """Credencial física de un colaborador para autenticación en piso de producción.

    Abstrae el hardware periférico (RFID/QR/Barcode) — todos operan en modo HID
    e inyectan `badge_raw_value` como texto + Enter en el input activo.

    Iron Wall ADR: collaborator_id es soft FK (UUID sin DB constraint) porque
    hcm_collaborators vive en hcm_db (servicio separado). La resolución HTTP
    se hace al registrar el badge, no en cada scan.
    """
    __tablename__ = "mes_collaborator_badges"

    __table_args__ = (
        UniqueConstraint("badge_raw_value", "company_id", name="uq_badge_value_company"),
        Index("ix_badge_raw_value", "badge_raw_value"),
        Index("ix_badge_collaborator", "collaborator_id"),
    )

    # Soft FK — no DB constraint (hcm_collaborators está en hcm_db)
    collaborator_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    # Denormalizado para evitar llamada HTTP en cada scan (degraded mode)
    collaborator_name: Mapped[str] = mapped_column(String(200), nullable=False)
    employee_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    badge_raw_value: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_type: Mapped[str] = mapped_column(String(20), nullable=False)  # BARCODE | QR | RFID

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
