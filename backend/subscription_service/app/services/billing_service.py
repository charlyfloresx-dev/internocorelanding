import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Any
from app.domain.repositories.subscription_repository import ISubscriptionRepository
from app.infrastructure.interfaces.payment_provider import IPaymentProvider
from app.core.enums import SubscriptionStatus
from common.config import settings


logger = logging.getLogger(__name__)


class BillingService:
    """
    Coordina la lógica de negocio de facturación y orquestación con Stripe.
    """

    def __init__(self, repo: ISubscriptionRepository, payment_provider: IPaymentProvider):
        self.repo = repo
        self.payment_provider = payment_provider

    async def create_membership_session(self, company_id: uuid.UUID, user_email: str) -> str:
        """
        Inicia el proceso de suscripción creando una sesión de pago.
        """
        # 1. Validar si ya tiene suscripción ACTIVE
        subscription = await self.repo.get_subscription_by_company(company_id)
        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            logger.warning(f"Empresa {company_id} intentó suscribirse teniendo ya una suscripción activa.")

        # 2. Crear sesión en el proveedor de pagos
        # Usamos un plan_id por defecto o el configurado
        plan_id = settings.stripe.int_stripe_product_id
        success_url = f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{settings.FRONTEND_URL}/billing/cancel"
        
        client_secret = await self.payment_provider.create_checkout_session(
            company_id=company_id,
            plan_id=plan_id,
            success_url=success_url,
            cancel_url=cancel_url
        )

        # 3. Registrar Intento en Auditoría
        audit_data = {
            "company_id": company_id,
            "subscription_id": uuid.uuid4(),
            "event_type": "BILLING_SESSION_CREATED",
            "before_state": {},
            "after_state": {"status": "PENDING", "user": user_email},
            "reason": "User initiated checkout session."
        }
        await self.repo.save_audit_log(audit_data)

        return client_secret

    async def activate_subscription(
        self, 
        company_id: uuid.UUID, 
        stripe_sub_id: str, 
        stripe_customer_id: str,
        current_period_end: datetime,
        customer_name: str = "Cliente",
        customer_email: Optional[str] = None
    ) -> bool:
        """
        Activa o actualiza una suscripción tras un pago exitoso.
        """
        subscription = await self.repo.get_subscription_by_company(company_id)

        before_state = {}
        if subscription:
            before_state = {
                "status": subscription.status,
                "stripe_subscription_id": subscription.stripe_subscription_id,
                "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
            }
            update_data = {
                "status": SubscriptionStatus.ACTIVE,
                "stripe_subscription_id": stripe_sub_id,
                "stripe_customer_id": stripe_customer_id,
                "current_period_end": current_period_end,
                "readonly": False
            }
            await self.repo.update_subscription(stripe_sub_id, update_data)
        else:
            plans = await self.repo.get_active_plans()
            if not plans:
                logger.error(f"No se encontró ningún Plan en la DB para activar suscripción de {company_id}")
                return False
            
            plan = plans[0]
            subscription_data = {
                "company_id": company_id,
                "plan_id": plan.id,
                "status": SubscriptionStatus.ACTIVE,
                "stripe_subscription_id": stripe_sub_id,
                "stripe_customer_id": stripe_customer_id,
                "current_period_end": current_period_end,
                "start_date": datetime.now(timezone.utc),
                "readonly": False
            }
            subscription = await self.repo.create_subscription(subscription_data)

        # Registrar en Auditoría
        audit_data = {
            "company_id": company_id,
            "subscription_id": subscription.id,
            "event_type": "PAYMENT_SUCCESS",
            "before_state": before_state,
            "after_state": {
                "status": "ACTIVE",
                "stripe_subscription_id": stripe_sub_id,
                "current_period_end": current_period_end.isoformat()
            },
            "reason": "Payment success confirmed via provider."
        }
        await self.repo.save_audit_log(audit_data)
        
        return True

    async def handle_payment_failed(
        self,
        stripe_sub_id: str,
        stripe_customer_id: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> bool:
        """
        Transiciona una suscripción al estado PAST_DUE tras un cobro fallido,
        y delega el envío de notificaciones.
        """
        subscription = await self.repo.get_subscription_by_stripe_id(stripe_sub_id)
        if not subscription:
            logger.error(f"Suscripción {stripe_sub_id} no encontrada localmente.")
            return False

        before_state = {
            "status": subscription.status,
            "stripe_subscription_id": subscription.stripe_subscription_id
        }

        # Actualizar a PAST_DUE
        update_data = {
            "status": SubscriptionStatus.PAST_DUE,
            "status_updated_at": datetime.now(timezone.utc),
            "readonly": False  # PAST_DUE retains full access for the first 3 days
        }
        await self.repo.update_subscription(stripe_sub_id, update_data)

        # Registrar en Auditoría
        audit_data = {
            "company_id": subscription.company_id,
            "subscription_id": subscription.id,
            "event_type": "PAYMENT_FAILED",
            "before_state": before_state,
            "after_state": {
                "status": "PAST_DUE"
            },
            "reason": "Invoice payment failed webhook received."
        }
        await self.repo.save_audit_log(audit_data)

        # --- OUTBOX PATTERN: Publish Notification Event ---
        # Assuming a message broker is configured, we dispatch an event.
        # This will be picked up by the notification_service.
        event_payload = {
            "company_id": str(subscription.company_id),
            "event_type": "SUBSCRIPTION_PAYMENT_FAILED",
            "email": customer_email,
            "stripe_customer_id": stripe_customer_id
        }
        # e.g., await self.message_broker.publish("billing.events", event_payload)
        logger.info(f"Published Notification Event for PAST_DUE: {event_payload}")

        return True
