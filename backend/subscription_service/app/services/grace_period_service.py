import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.subscription import Subscription, AuditSubscriptionLog
from app.core.enums import SubscriptionStatus

logger = logging.getLogger(__name__)

class GracePeriodService:
    """
    Servicio encargado de auditar y degradar suscripciones
    que no han pagado, siguiendo las reglas de negocio de Phase 19.
    """

    @classmethod
    async def process_grace_periods(cls, db: AsyncSession):
        """
        Ejecuta la evaluación diaria de suscripciones en PAST_DUE y RESTRICTED.
        Reglas:
        - PAST_DUE > 4 días -> RESTRICTED (readonly)
        - RESTRICTED > 7 días en total -> UNPAID (bloqueo total)
        """
        logger.info("Iniciando auditoría de Grace Period (Fase 19)...")
        now = datetime.now(timezone.utc)
        
        # 1. Evaluate PAST_DUE -> RESTRICTED (Day 4)
        past_due_threshold = now - timedelta(days=4)
        stmt_past_due = select(Subscription).where(
            Subscription.status == SubscriptionStatus.PAST_DUE,
            Subscription.status_updated_at <= past_due_threshold
        )
        
        result = await db.execute(stmt_past_due)
        past_due_subs = result.scalars().all()
        
        for sub in past_due_subs:
            logger.info(f"Degradando suscripción {sub.id} a RESTRICTED (Grace Period excedido).")
            before_state = {"status": sub.status, "readonly": sub.readonly}
            
            sub.status = SubscriptionStatus.RESTRICTED
            sub.status_updated_at = now
            sub.readonly = True
            
            audit = AuditSubscriptionLog(
                company_id=sub.company_id,
                subscription_id=sub.id,
                event_type="GRACE_PERIOD_DEGRADATION",
                before_state=before_state,
                after_state={"status": "RESTRICTED", "readonly": True},
                reason="Auto-transition: PAST_DUE exceeded 4 days."
            )
            db.add(audit)
            
        # 2. Evaluate RESTRICTED -> UNPAID (Day 8+)
        # Note: If it transitioned to RESTRICTED 4 days ago, and 3 more days pass, that's 7 days total.
        # But since we updated status_updated_at when it moved to RESTRICTED, the threshold is 3 days.
        restricted_threshold = now - timedelta(days=3)
        stmt_restricted = select(Subscription).where(
            Subscription.status == SubscriptionStatus.RESTRICTED,
            Subscription.status_updated_at <= restricted_threshold
        )
        
        result2 = await db.execute(stmt_restricted)
        restricted_subs = result2.scalars().all()
        
        for sub in restricted_subs:
            logger.info(f"Degradando suscripción {sub.id} a UNPAID (Lockdown total).")
            before_state = {"status": sub.status, "readonly": sub.readonly}
            
            sub.status = SubscriptionStatus.UNPAID
            sub.status_updated_at = now
            # stays readonly, but UNPAID triggers total block in middleware
            
            audit = AuditSubscriptionLog(
                company_id=sub.company_id,
                subscription_id=sub.id,
                event_type="GRACE_PERIOD_LOCKDOWN",
                before_state=before_state,
                after_state={"status": "UNPAID"},
                reason="Auto-transition: RESTRICTED exceeded 3 days."
            )
            db.add(audit)

        await db.commit()
        logger.info(f"Auditoría de Grace Period completada. Procesadas: PAST_DUE->RESTRICTED ({len(past_due_subs)}), RESTRICTED->UNPAID ({len(restricted_subs)})")
