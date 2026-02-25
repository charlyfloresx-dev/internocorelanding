import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.subscription import Subscription, Plan, Entitlement
from app.core.enums import SubscriptionStatus
from app.services.audit import AuditService

class StartTrialCommand:
    @staticmethod
    async def execute(
        db: AsyncSession, 
        company_id: uuid.UUID, 
        plan_name: str = "Plan Básico",
        user_id: Optional[uuid.UUID] = None,
        user_ip: Optional[str] = None
    ):
        # 1. Buscar el plan
        result = await db.execute(select(Plan).where(Plan.name == plan_name))
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError(f"Plan {plan_name} no encontrado")

        # 2. Crear suscripción
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            company_id=company_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            start_date=now,
            end_date=now + timedelta(days=plan.trial_days),
            created_by=None # En handshake interno podría no haber user context
        )
        db.add(subscription)
        await db.flush()

        # 3. Activar Entitlements (SSOT)
        for module_code in plan.modules:
            entitlement = Entitlement(
                company_id=company_id,
                module_code=module_code,
                is_enabled=True,
                source_subscription_id=subscription.id
            )
            db.add(entitlement)

        # 4. Auditoría
        await AuditService.log_change(
            db=db,
            company_id=company_id,
            subscription_id=subscription.id,
            event_type="START_TRIAL",
            after_state={
                "plan_id": str(plan.id),
                "status": subscription.status,
                "end_date": subscription.end_date.isoformat(),
                "modules": plan.modules
            },
            reason=f"Auto-generación de trial: {plan_name}",
            user_id=user_id,
            user_ip=user_ip
        )
        
        await db.commit()
        return subscription
