import uuid
from datetime import date
from typing import Optional

from sqlalchemy import String, Boolean, UUID, UniqueConstraint, ForeignKey, Index, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.infrastructure.models.base import MultiTenantBase


class Collaborator(MultiTenantBase):
    """
    Physical identity of an operator on the production floor.

    Phase 50: Expanded with full industrial identity compliance fields.
    - Fiscal Identity (RFC/CURP) validated via Pydantic, stored as-is.
    - Cross-border credentials have explicit expiry dates (not booleans).
    - HazMat & Medical Certificate support SCT (Mexico) and DOT (USA) compliance.
    - emergency_contact stored as validated JSONB for frontend signal hydration.

    Inherits from MultiTenantBase → company_id + tenant_id + group_id are mandatory.

    Security:
      - rfid_tag: SHA-256 hash (with static salt). Stored as HEX. Indexed for O(1) scan lookups.
      - pin_code: Bcrypt hash. Slower but stronger for manual PIN entry.

    Hierarchy:
      - supervisor_id: Self-referencing FK. Enables Recursive CTEs for reporting trees.
        Supervisors bypass the Warehouse Lock in the Inventory Service (is_supervisor claim).
    """
    __tablename__ = "collaborators"

    # ── Core Identity ──────────────────────────────────────────────────────────

    # Legacy compatibility: alphanumeric employee number, unique per company (see __table_args__)
    internal_id: Mapped[str] = mapped_column(String(50), nullable=False)

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department", backref="collaborators", lazy="selectin"
    )
    translation_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Payroll classification (from legacy: Direct=True, Indirect=False)
    is_direct: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # The collaborator's "home" warehouse — injected as `wid` in the JWT
    home_warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # ── Organizational Hierarchy ───────────────────────────────────────────────

    supervisor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    supervisor: Mapped[Optional["Collaborator"]] = relationship(
        "Collaborator",
        primaryjoin="Collaborator.id == Collaborator.supervisor_id",
        remote_side="Collaborator.id",
        foreign_keys=[supervisor_id],
        lazy="select",
    )

    # ── Hardware Credentials ───────────────────────────────────────────────────

    rfid_tag: Mapped[Optional[str]] = mapped_column(
        String(64),   # SHA-256 hex digest is always 64 chars
        nullable=True,
        index=True,   # Critical: O(1) hardware scan lookups
    )
    pin_code: Mapped[Optional[str]] = mapped_column(
        String(128),  # Bcrypt hash length
        nullable=True,
    )

    # ── [Phase 50] ERP Integration ─────────────────────────────────────────────

    # Infor M3 operator identifier for WMS bridge
    m3_operator_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)

    # ── [Phase 50] Fiscal Identity (Mexico) ───────────────────────────────────
    # Values are validated via Pydantic (regex from legacy .NET) before reaching the DB.

    # Registro Federal de Contribuyentes — Persona Física (12-13 chars)
    rfc: Mapped[Optional[str]] = mapped_column(String(13), nullable=True, unique=False)

    # Clave Única de Registro de Población (18 chars)
    curp: Mapped[Optional[str]] = mapped_column(String(18), nullable=True, unique=False)

    # Número de Seguro Social (IMSS) — 11 digits
    nss: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)

    # ── [Phase 50] Cross-Border Credentials ───────────────────────────────────
    # All expiry dates use SQLAlchemy Date to avoid timezone conflicts in "day-level" validations.

    # USA Visa Láser / B1-B2 visa
    visa_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    visa_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # CBP FAST / Sentry card
    sentry_id: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Commercial driver's license (CDL / Licencia Federal)
    driver_license_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    driver_license_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ── [Phase 50] HazMat & Medical Compliance (SCT/DOT) ──────────────────────

    # Can this operator transport hazardous materials?
    hazardous_material_certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # SCT (Mexico) / DOT (USA) commercial medical certificate expiry
    medical_certificate_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Last antidoping test — required for C-TPAT / OEA audits
    last_drug_test_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ── [Phase 50] Industrial Safety ──────────────────────────────────────────

    # Blood type for industrial accident first response (e.g., "O+", "AB-")
    blood_type: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    # ── [Phase 44] Media Assets ───────────────────────────────────────────────
    
    # Path inside the bucket: {company_id}/hr/collaborators/{uuid}.jpg
    photo_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Identidad Unificada ────────────────────────────────────────────────────
    
    # Vincula al colaborador industrial con su identidad de usuario web
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # JSONB: {name, relationship, phone, alternative_phone}
    # Standardized schema enforced at the Pydantic layer (EmergencyContact schema)
    emergency_contact: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Constraints & Indexes ──────────────────────────────────────────────────

    __table_args__ = (
        # Enforce uniqueness of internal_id per company (multi-tenant safe)
        UniqueConstraint("internal_id", "company_id", name="uq_collaborator_internal_id_company"),
        # Compound index for RFID lookups within a company scope
        # This prevents cross-tenant badge collision with generic RFID card series
        Index("ix_collaborator_rfid_company", "rfid_tag", "company_id"),
        # M3 operator ID scoped by tenant
        Index("ix_collaborator_m3_company", "m3_operator_id", "company_id"),
    )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Collaborator id={self.id} internal_id={self.internal_id} name={self.full_name}>"
