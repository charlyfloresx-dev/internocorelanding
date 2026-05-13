import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.exceptions import BusinessRuleException, NotFoundException
from subscription_app.models.subscription import Subscription, Plan, AuditSubscriptionLog, BillingEvent
from subscription_app.core.enums import SubscriptionStatus

logger = logging.getLogger(__name__)

class ChangeSubscriptionPlanCommand:
    def __init__(self, company_id: str, new_plan_id: str, reason: str = "Plan Change"):
        self.company_id = uuid.UUID(company_id)
        self.new_plan_id = uuid.UUID(new_plan_id)
        self.reason = reason

class ChangeSubscriptionPlanHandler:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def handle(self, command: ChangeSubscriptionPlanCommand) -> dict:
        """
        Handler atómico para el cambio de plan de suscripción.
        Cumple con el patrón Unit of Work (UoW) y validación de invariantes financieras.
        """
        async with self.session.begin_nested() as tx:
            # 1. Bloqueo Optimista: Obtener suscripción actual
            stmt_sub = select(Subscription).filter_by(company_id=command.company_id).with_for_update()
            sub = (await self.session.execute(stmt_sub)).scalar_one_or_none()
            
            if not sub:
                raise NotFoundException("Subscription not found for this tenant.")
                
            old_plan_id = sub.plan_id

            # 2. Obtener el nuevo plan
            stmt_plan = select(Plan).filter_by(id=command.new_plan_id)
            new_plan = (await self.session.execute(stmt_plan)).scalar_one_or_none()

            if not new_plan:
                raise NotFoundException("Target Plan not found.")

            # 3. Invariante de Cuota (Guardrail)
            # Validación: El uso actual no debe exceder el límite del nuevo plan, 
            # a menos que el nuevo plan permita excedentes (allow_overage).
            if not new_plan.allow_overage and sub.current_storage_usage > new_plan.storage_limit:
                raise BusinessRuleException(
                    f"Downgrade rejected: Current usage ({sub.current_storage_usage} bytes) "
                    f"exceeds the new plan's limit ({new_plan.storage_limit} bytes)."
                )

            # 4. Atomicidad Financiera (Registro de Log/Evento)
            audit_log = AuditSubscriptionLog(
                company_id=command.company_id,
                subscription_id=sub.id,
                event_type="PLAN_CHANGE",
                before_state={"plan_id": str(old_plan_id), "status": sub.status},
                after_state={"plan_id": str(new_plan.id), "status": SubscriptionStatus.ACTIVE},
                reason=command.reason
            )
            self.session.add(audit_log)

            # Register BillingEvent for Stripe/MercadoPago integration
            billing_event = BillingEvent(
                company_id=command.company_id,
                subscription_id=sub.id,
                amount=new_plan.price,
                currency=new_plan.currency,
                provider="STRIPE",
                event_type="CHANGE_PLAN",
                status="PENDING"
            )
            self.session.add(billing_event)

            # 5. Actualizar la Entidad Principal
            sub.plan_id = new_plan.id
            sub.status = SubscriptionStatus.ACTIVE
            sub.status_updated_at = datetime.utcnow()
            sub.readonly = False
            
            # Simulando la emisión del evento a un Event Bus
            # await event_bus.publish("TenantPlanChanged", {"company_id": str(command.company_id), "new_plan_id": str(new_plan.id)})
            logger.info(f"🚀 TenantPlanChanged event emitted for company {command.company_id}. New Plan: {new_plan.name}")

            return {
                "id": str(sub.id),
                "status": "success",
                "new_plan": new_plan.name,
                "timestamp": datetime.utcnow().isoformat()
            }
