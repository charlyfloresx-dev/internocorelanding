import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository
from subscription_app.core.enums import SubscriptionStatus
from common.context import request_context


class StartTrialCommand:
    def __init__(self, repo: ISubscriptionRepository):
        self.repo = repo

    async def execute(
        self, 
        company_id: uuid.UUID, 
        plan_name: str = "Plan Básico",
        user_id: Optional[uuid.UUID] = None,
        user_ip: Optional[str] = None
    ):
        # 1. Buscar el plan
        plan = await self.repo.get_plan_by_stripe_product(plan_name)
        if not plan:
            raise ValueError(f"Plan {plan_name} no encontrado")

        # 2. Crear suscripción
        now = datetime.now(timezone.utc)
        ctx = request_context.get()
        effective_user_id = user_id or (ctx.user_id if ctx else None)

        subscription_data = {
            "company_id": company_id,
            "plan_id": plan.id,
            "status": SubscriptionStatus.TRIAL,
            "start_date": now,
            "end_date": now + timedelta(days=plan.trial_days),
            "current_storage_usage": 0,
            "created_by": effective_user_id
        }
        subscription = await self.repo.create_subscription(subscription_data)

        # 3. Auditoría (se podría inyectar AuditService también, pero mantengamos simple por ahora si AuditService no es estático)
        # Para el refactor, asumo que AuditService también se limpiará.
        
        return subscription
