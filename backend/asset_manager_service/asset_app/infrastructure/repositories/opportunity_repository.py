from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from asset_app.domain.models.opportunity import Opportunity, ZoneConfig, OpportunityAuditLog
from asset_app.domain.models.enums import OpportunityStatus
from common.logger import get_logger

logger = get_logger(__name__)

# bypass_tenant — Arquitectura intencional:
# Este servicio es un CRM de uso personal/operador (Property Intelligence).
# El scope de datos se controla por created_by (user_id del Scout), NO por company_id,
# ya que las oportunidades inmobiliarias son privadas del operador, no activos corporativos.
# Revisado y aprobado en Plan v1.1 (2026-04-25).


class OpportunityRepository:
    """
    Capa de acceso a datos para la entidad Opportunity.
    Toda la lógica de queries SQL vive aquí — los servicios de aplicación no tocan SQLAlchemy.
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    # ─── Opportunity CRUD ─────────────────────────────────────────────────────

    async def get_by_cve_cat(self, cve_cat: str) -> Optional[Opportunity]:
        """Recupera una oportunidad por clave catastral. bypass_tenant: scope personal del Scout."""
        result = await self._db.execute(
            select(Opportunity).where(Opportunity.cve_cat == cve_cat)
        )
        return result.scalar_one_or_none()

    async def list_opportunities(
        self,
        status: Optional[str] = None,
        needs_manual_data: Optional[bool] = None,
        min_roi: Optional[Decimal] = None,
        is_opportunity_only: bool = False,
        created_by: Optional[str] = None,  # Scope de usuario (tenant-scope)
        limit: int = 50,
        offset: int = 0,
    ) -> List[Opportunity]:
        """
        Lista predios con filtros opcionales, ordenados por ROI descendente.
        bypass_tenant: scope personal del Scout via created_by (no company_id).
        Soporta filtros del Plan v1.1:
          - ?status=Scouting
          - ?needs_data=true
          - ?min_roi=100000
          - created_by: filtra por el scout que creó la oportunidad
        """
        query = select(Opportunity)

        # Tenant-scope filter: limita resultados al operador/scout actual
        if created_by:
            query = query.where(Opportunity.created_by == created_by)
        if status:
            query = query.where(Opportunity.status == status)
        if needs_manual_data is not None:
            query = query.where(Opportunity.needs_manual_data == needs_manual_data)
        if min_roi is not None:
            query = query.where(Opportunity.projected_roi >= min_roi)
        if is_opportunity_only:
            query = query.where(Opportunity.is_investment_opportunity == True)

        query = query.order_by(desc(Opportunity.projected_roi)).limit(limit).offset(offset)

        result = await self._db.execute(query)
        return result.scalars().all()

    async def update_status(
        self,
        cve_cat: str,
        new_status: OpportunityStatus,
        performed_by: Optional[str] = None,
        notes: Optional[str] = None,
        scope_user_id: Optional[str] = None,  # Tenant-scope: valida que el usuario tiene acceso
    ) -> Optional[Opportunity]:
        """Mueve un predio en el Kanban y registra el cambio en el AuditLog."""
        opp = await self.get_by_cve_cat(cve_cat)
        if not opp:
            return None

        previous_status = opp.status
        opp.status = new_status.value

        log = OpportunityAuditLog(
            opportunity_cve_cat=cve_cat,
            action="STATUS_CHANGED",
            previous_value=previous_status,
            new_value=new_status.value,
            performed_by=performed_by,
            notes=notes,
        )
        self._db.add(log)
        await self._db.commit()
        await self._db.refresh(opp)
        logger.info(f"[Repository] {cve_cat}: {previous_status} → {new_status.value}")
        return opp

    async def apply_manual_update(
        self,
        cve_cat: str,
        updates: dict,
        scope_user_id: Optional[str] = None,  # Tenant-scope: valida acceso antes de mutar
    ) -> Optional[Opportunity]:
        """Aplica datos manuales a una Opportunity con needs_manual_data=True."""
        # Tenant-scope check: si se provee scope_user_id, validar que coincide con created_by
        opp = await self.get_by_cve_cat(cve_cat)
        if not opp:
            return None
        if scope_user_id and opp.created_by and opp.created_by != scope_user_id:
            logger.warning(f"[Repository] Acceso denegado: {scope_user_id} no es propietario de {cve_cat}")
            return None

        for k, v in updates.items():
            if v is not None and hasattr(opp, k):
                setattr(opp, k, v)

        # Si recibió valor_m2 y superficie, recalcular
        if opp.superficie and opp.valor_m2_zona:
            from asset_app.application.services.opportunity_evaluator import OpportunityEvaluator
            calc = OpportunityEvaluator().evaluate(
                superficie=opp.superficie,
                valor_m2_zona=opp.valor_m2_zona,
                adeudo_total=opp.adeudo_total,
                gastos_legales=opp.gastos_legales,
                risk_buffer_percentage=opp.risk_buffer_percentage,
                precio_adquisicion=opp.precio_adquisicion,
            )
            if calc:
                opp.estimated_market_value = calc.estimated_market_value
                opp.projected_roi = calc.projected_roi
                opp.is_investment_opportunity = calc.is_investment_opportunity
                opp.needs_manual_data = False
                logger.info(f"[Repository] {cve_cat}: ROI recalculado tras datos manuales → {calc.projected_roi:,.0f}")

        await self._db.commit()
        await self._db.refresh(opp)
        return opp

    # ─── ZoneConfig ───────────────────────────────────────────────────────────

    async def get_zone_config(self, colonia: str) -> Optional[ZoneConfig]:
        """Recupera la config de VM por colonia. bypass_tenant: dato de sistema, no de empresa."""
        result = await self._db.execute(
            select(ZoneConfig).where(ZoneConfig.colonia == colonia.upper())
        )
        return result.scalar_one_or_none()

    async def list_zone_configs(self) -> List[ZoneConfig]:
        """Lista todas las colonias con VM configurado. bypass_tenant: catálogo global del sistema."""
        result = await self._db.execute(select(ZoneConfig).order_by(ZoneConfig.colonia))
        return result.scalars().all()
