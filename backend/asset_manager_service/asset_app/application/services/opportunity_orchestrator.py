"""
OpportunityOrchestrator — Service Orchestrator

Recibe el payload del /full-report (vía BackgroundTask) y decide:
  - Si hay suficientes datos para calcular ROI → crea/actualiza Opportunity.
  - Si faltan datos críticos → crea registro con needs_manual_data=True.
  - Si el predio ya existe → actualiza con datos más frescos (upsert).
"""
from decimal import Decimal
from typing import Optional
from datetime import timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from asset_app.domain.models.opportunity import Opportunity, ZoneConfig, OpportunityAuditLog
from asset_app.application.schemas.opportunity import FullReportInput
from asset_app.application.services.opportunity_evaluator import OpportunityEvaluator
from common.logger import get_logger

logger = get_logger(__name__)


class OpportunityOrchestrator:
    """
    Orquestador principal del Asset Manager.
    Recibe datos crudos del WMS/RPPC y los transforma en una Opportunity evaluada.
    """

    def __init__(self, db: AsyncSession):
        self._db = db
        self._evaluator = OpportunityEvaluator()

    async def process_full_report(self, data: FullReportInput) -> Opportunity:
        """
        Entry point principal — llamado por la BackgroundTask en gis_validator.

        1. Busca ZoneConfig para la colonia (o usa override manual).
        2. Corre el Financial Engine.
        3. Upsert del registro Opportunity.
        4. Registra en AuditLog.
        """
        # ── 1. Resolver Valor de Mercado ──────────────────────────────────
        valor_m2 = await self._resolve_valor_m2(
            colonia=data.colonia,
            override=data.valor_m2_zona_override
        )

        # ── 2. Evaluar Financieramente ─────────────────────────────────────
        calc = None
        needs_manual = False

        if valor_m2 and data.superficie:
            calc = self._evaluator.evaluate(
                superficie=Decimal(str(data.superficie)),
                valor_m2_zona=valor_m2,
                adeudo_total=data.adeudo_total,
                gastos_legales=data.gastos_legales,
                risk_buffer_percentage=data.risk_buffer_percentage,
                precio_adquisicion=None,  # Se llena en negociación
            )
        else:
            needs_manual = True
            logger.warning(
                f"[Orchestrator] Predio {data.cve_cat}: faltan datos para calcular ROI. "
                f"valor_m2={valor_m2}, superficie={data.superficie} — marcado needs_manual_data=True."
            )

        # ── 3. Upsert de la Opportunity ────────────────────────────────────
        opportunity = await self._upsert_opportunity(data, valor_m2, calc, needs_manual)

        # ── 4. Registrar en AuditLog ──────────────────────────────────────
        log_entry = OpportunityAuditLog(
            opportunity_cve_cat=opportunity.cve_cat,
            action="REPORT_PROCESSED",
            previous_value=None,
            new_value=f"ROI={calc.projected_roi if calc else 'N/A'} | needs_manual={needs_manual}",
            performed_by=data.created_by,
            notes=f"Procesado automáticamente vía BackgroundTask desde /full-report."
        )
        self._db.add(log_entry)
        await self._db.commit()
        await self._db.refresh(opportunity)

        return opportunity

    async def _resolve_valor_m2(
        self,
        colonia: Optional[str],
        override: Optional[Decimal]
    ) -> Optional[Decimal]:
        """
        Prioridad: override manual > ZoneConfig en DB > None.
        Si el usuario ingresó un override Y la colonia no tiene config, lo persiste.
        """
        if override:
            if colonia:
                await self._learn_zone_value(colonia, override)
            return override

        if not colonia:
            return None

        result = await self._db.execute(
            select(ZoneConfig).where(ZoneConfig.colonia == colonia.upper())
        )
        zone = result.scalar_one_or_none()
        return Decimal(str(zone.valor_m2)) if zone else None

    async def _learn_zone_value(self, colonia: str, valor_m2: Decimal) -> None:
        """Persiste el valor de m² de la zona para futuros predios en la misma colonia."""
        result = await self._db.execute(
            select(ZoneConfig).where(ZoneConfig.colonia == colonia.upper())
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.valor_m2 = valor_m2
            existing.source = "manual_override"
        else:
            self._db.add(ZoneConfig(
                colonia=colonia.upper(),
                valor_m2=valor_m2,
                source="manual",
            ))
        await self._db.flush()
        logger.info(f"[Orchestrator] ZoneConfig persistido: colonia={colonia.upper()} valor_m2={valor_m2}")

    async def _upsert_opportunity(
        self,
        data: FullReportInput,
        valor_m2: Optional[Decimal],
        calc,
        needs_manual: bool,
    ) -> Opportunity:
        """Crea o actualiza el registro de Opportunity (upsert por cve_cat)."""
        result = await self._db.execute(
            select(Opportunity).where(Opportunity.cve_cat == data.cve_cat)
        )
        existing = result.scalar_one_or_none()

        fields = {
            "lat": data.lat,
            "lng": data.lng,
            "propietario_rppc": data.propietario,
            "folio_real": data.folio_real,
            "superficie": Decimal(str(data.superficie)) if data.superficie else None,
            "direccion_catastral": data.direccion_catastral,
            "colonia": data.colonia.upper() if data.colonia else None,
            "adeudo_total": data.adeudo_total,
            "ultimo_pago": data.ultimo_pago,
            "valor_m2_zona": valor_m2,
            "gastos_legales": data.gastos_legales or Decimal("50000"),
            "risk_buffer_percentage": data.risk_buffer_percentage or Decimal("0.10"),
            "needs_manual_data": needs_manual,
        }

        if calc:
            fields["estimated_market_value"] = calc.estimated_market_value
            fields["projected_roi"] = calc.projected_roi
            fields["is_investment_opportunity"] = calc.is_investment_opportunity

        if existing:
            for k, v in fields.items():
                if v is not None:  # Solo actualiza campos que tuvieron datos frescos
                    setattr(existing, k, v)
            opp = existing
        else:
            opp = Opportunity(cve_cat=data.cve_cat, created_by=data.created_by, **fields)
            self._db.add(opp)

        await self._db.flush()
        return opp
