import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, String, Numeric, Boolean, DateTime, Text,
    Integer, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class ZoneConfig(Base):
    """
    Valor de Mercado por m² configurado para una colonia/zona.
    El sistema aprende este valor cuando un usuario lo ingresa manualmente
    en la primera consulta de esa zona.
    """
    __tablename__ = "zone_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    colonia = Column(String(200), nullable=False, unique=True, index=True)
    municipio = Column(Integer, nullable=False, default=2)  # 2 = Tijuana
    valor_m2 = Column(Numeric(12, 2), nullable=False)
    source = Column(String(50), default="manual")  # 'manual' | 'scraped' | 'api'
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(36), nullable=True)

    def __repr__(self):
        return f"<ZoneConfig colonia={self.colonia} valor_m2={self.valor_m2}>"


class Opportunity(Base):
    """
    Predio identificado como potencial activo en problemas (Distressed Real Estate Asset).
    El corazón del CRM de Interno Assets.
    """
    __tablename__ = "opportunities"

    # ─── Identidad Catastral ──────────────────────────────────────────────
    cve_cat = Column(String(50), primary_key=True)
    lat = Column(Numeric(11, 7), nullable=True)
    lng = Column(Numeric(11, 7), nullable=True)
    direccion_catastral = Column(String(300), nullable=True)
    colonia = Column(String(200), nullable=True)
    superficie = Column(Numeric(10, 2), nullable=True)   # m²

    # ─── Datos del Propietario (RPPC) ────────────────────────────────────
    propietario_rppc = Column(String(300), nullable=True)
    folio_real = Column(String(100), nullable=True)
    propietario_contacto = Column(JSON, nullable=True)  # free-form / skip-trace future
    # TODO: Fase futura — integrar API de Skip Tracing para buscar
    # número de teléfono o dirección de notificación del titular.

    # ─── Datos Financieros ────────────────────────────────────────────────
    adeudo_total = Column(Numeric(14, 2), nullable=True)
    ultimo_pago = Column(DateTime(timezone=True), nullable=True)
    valor_m2_zona = Column(Numeric(12, 2), nullable=True)
    estimated_market_value = Column(Numeric(14, 2), nullable=True)
    precio_adquisicion = Column(Numeric(14, 2), nullable=True)  # PA: precio pactado
    gastos_legales = Column(Numeric(12, 2), nullable=True, default=Decimal("50000"))
    risk_buffer_percentage = Column(Numeric(5, 4), nullable=False, default=Decimal("0.10"))  # 10%
    projected_roi = Column(Numeric(14, 2), nullable=True)
    is_investment_opportunity = Column(Boolean, default=False, index=True)

    # ─── Pipeline Kanban ─────────────────────────────────────────────────
    status = Column(
        SAEnum("Scouting", "Due Diligence", "Negociación", "Adjudicación/Cierre", "Venta", "Descartado", name="opportunity_status"),
        default="Scouting",
        nullable=False,
        index=True
    )
    legal_status = Column(
        SAEnum("Libre", "Intestado", "Litigio", "Embargado", "Desconocido", name="legal_status"),
        default="Desconocido",
        nullable=False
    )

    # ─── Flags de Calidad de Datos ────────────────────────────────────────
    needs_manual_data = Column(Boolean, default=False, index=True)
    notes = Column(Text, nullable=True)

    # ─── Auditoría ────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(36), nullable=True)   # user_id del Scout

    # ─── Relaciones ──────────────────────────────────────────────────────
    audit_logs = relationship("OpportunityAuditLog", back_populates="opportunity", cascade="all, delete-orphan")

    @property
    def days_in_pipeline(self) -> int:
        """Días transcurridos desde que se detectó la oportunidad."""
        if not self.created_at:
            return 0
        now = datetime.now(timezone.utc)
        created = self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc)
        return (now - created).days

    def __repr__(self):
        return f"<Opportunity cve_cat={self.cve_cat} status={self.status} roi={self.projected_roi}>"


class OpportunityAuditLog(Base):
    """
    Bitácora de cambios en el pipeline (quién movió el status y cuándo).
    """
    __tablename__ = "opportunity_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_cve_cat = Column(String(50), ForeignKey("opportunities.cve_cat", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False)           # ej. "STATUS_CHANGED"
    previous_value = Column(String(200), nullable=True)
    new_value = Column(String(200), nullable=True)
    performed_by = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    opportunity = relationship("Opportunity", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.opportunity_cve_cat}>"
