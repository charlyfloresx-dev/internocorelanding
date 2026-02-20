import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from common.models.base_models import MultiTenantBase

class Facility(MultiTenantBase):
    """Planta o instalación física."""
    __tablename__ = "mes_facilities"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    areas: Mapped[List["ProductionArea"]] = relationship(back_populates="facility")

class ProductionArea(MultiTenantBase):
    """Área específica dentro de una planta (ej. VSM, Maquinado)."""
    __tablename__ = "mes_production_areas"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    facility_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_facilities.id"), nullable=False)

    facility: Mapped["Facility"] = relationship(back_populates="areas")
    resources: Mapped[List["Resource"]] = relationship(back_populates="area")

class Resource(MultiTenantBase):
    """La unidad física (Línea/Célula/Cámara)."""
    __tablename__ = "mes_resources"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    capacity_per_hour: Mapped[float] = mapped_column(Float, default=0.0)
    default_labor: Mapped[int] = mapped_column(Integer, default=1) # Personal base/planeado
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("mes_production_areas.id"), nullable=True)
    
    # Configuración de paros/descansos
    break_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    # Relaciones
    area: Mapped[Optional["ProductionArea"]] = relationship(back_populates="resources")
    results: Mapped[List["ResourceResult"]] = relationship(back_populates="resource")

class ResourceResult(MultiTenantBase):
    """El 'Contenedor de Turno' / Production Result."""
    __tablename__ = "mes_resource_results"

    resource_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("mes_resources.id"), nullable=False)
    shift_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="OPEN") # OPEN, CLOSED
    planned_labor: Mapped[int] = mapped_column(Integer, default=1) # Personal planeado para este turno

    # Relaciones
    resource: Mapped["Resource"] = relationship(back_populates="results")
    ledger_entries: Mapped[List["ManufacturingLedger"]] = relationship(back_populates="production_result")
    downtimes: Mapped[List["Downtime"]] = relationship(back_populates="production_result")
    labors: Mapped[List["Labor"]] = relationship(back_populates="production_result")
