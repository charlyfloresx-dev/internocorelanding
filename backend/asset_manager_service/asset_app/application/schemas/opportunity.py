from decimal import Decimal
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field

from asset_app.domain.models.enums import OpportunityStatus, LegalStatus


# ─── ZoneConfig Schemas ───────────────────────────────────────────────────────

class ZoneConfigCreate(BaseModel):
    colonia: str
    municipio: int = 2
    valor_m2: Decimal = Field(..., gt=0, description="Valor de mercado por m² en MXN")


class ZoneConfigResponse(ZoneConfigCreate):
    id: str
    source: str
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Opportunity Schemas ──────────────────────────────────────────────────────

class FullReportInput(BaseModel):
    """
    Payload que llega desde el gis_validator /full-report vía BackgroundTask.
    Mapea exactamente los campos que devuelve el endpoint.
    """
    cve_cat: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    propietario: Optional[str] = None
    folio_real: Optional[str] = None
    superficie: Optional[float] = None
    direccion_catastral: Optional[str] = None
    colonia: Optional[str] = None
    adeudo_total: Optional[Decimal] = None
    ultimo_pago: Optional[datetime] = None
    # Permite que el usuario ingrese el VM manualmente si el sistema no conoce la zona
    valor_m2_zona_override: Optional[Decimal] = Field(None, description="VM manual si la colonia no está en ZoneConfig")
    gastos_legales: Optional[Decimal] = Field(None, description="Override de gastos legales (default: 50,000 MXN)")
    risk_buffer_percentage: Optional[Decimal] = Field(None, description="Buffer de riesgo (default: 10%)")
    created_by: Optional[str] = None


class OpportunityResponse(BaseModel):
    cve_cat: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    propietario_rppc: Optional[str] = None
    folio_real: Optional[str] = None
    superficie: Optional[float] = None
    direccion_catastral: Optional[str] = None
    colonia: Optional[str] = None
    adeudo_total: Optional[Decimal] = None
    valor_m2_zona: Optional[Decimal] = None
    estimated_market_value: Optional[Decimal] = None
    precio_adquisicion: Optional[Decimal] = None
    gastos_legales: Optional[Decimal] = None
    risk_buffer_percentage: Optional[Decimal] = None
    projected_roi: Optional[Decimal] = None
    is_investment_opportunity: bool = False
    needs_manual_data: bool = False
    status: OpportunityStatus = OpportunityStatus.SCOUTING
    legal_status: LegalStatus = LegalStatus.DESCONOCIDO
    days_in_pipeline: int = 0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OpportunityStatusUpdate(BaseModel):
    status: OpportunityStatus
    notes: Optional[str] = None


class OpportunityManualUpdate(BaseModel):
    """Permite completar datos faltantes manualmente (cuando needs_manual_data=True)."""
    valor_m2_zona: Optional[Decimal] = None
    adeudo_total: Optional[Decimal] = None
    precio_adquisicion: Optional[Decimal] = None
    gastos_legales: Optional[Decimal] = None
    legal_status: Optional[LegalStatus] = None
    propietario_contacto: Optional[Any] = None
    notes: Optional[str] = None
