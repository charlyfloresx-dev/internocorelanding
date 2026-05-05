import logging
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from subscription_app.models.subscription import Subscription
from subscription_app.core.config import settings
import uuid

logger = logging.getLogger(__name__)

class SubscriptionRecoveryService:
    @staticmethod
    async def sync_from_stripe_if_empty(db: AsyncSession):
        """
        Escanea la tabla subscriptions. Si está vacía, contacta a Stripe
        y recrea los registros usando la metadata (company_id).
        Esencial para la Operación de Rescate en la Fase 87.
        """
        if not settings.STRIPE_API_KEY:
            logger.warning("STRIPE_API_KEY no está configurada. Omitiendo Recovery Service.")
            return

        # Verificar si la tabla local está vacía
        stmt = select(func.count()).select_from(Subscription)
        result = await db.execute(stmt)
        count = result.scalar()

        if count > 0:
            logger.info("Subscription table not empty. Skipping Stripe Sync Recovery.")
            return

        logger.warning("Subscription table is empty! Initiating Stripe Sync Recovery...")
        stripe.api_key = settings.STRIPE_API_KEY

        # Ojo: Para escalar masivamente, se debe usar paginación.
        # Por ahora usaremos un limit de 100 asumiendo fase temprana.
        try:
            # Iterar sobre las suscripciones activas/past_due en Stripe
            subscriptions = stripe.Subscription.list(status="all", limit=100)
            recovered_count = 0

            for sub_stripe in subscriptions.data:
                customer = stripe.Customer.retrieve(sub_stripe.customer)
                
                # Extraemos el company_id de la metadata del Customer (o de la Subscripción)
                # Idealmente debería estar en la subscripción, pero revisamos ambos.
                company_id_str = sub_stripe.metadata.get("company_id") or customer.metadata.get("company_id")
                tenant_id_str = sub_stripe.metadata.get("tenant_id") or customer.metadata.get("tenant_id") or company_id_str

                if not company_id_str:
                    logger.warning(f"No company_id in metadata for Stripe Subscription {sub_stripe.id}. Skipping.")
                    continue
                
                try:
                    company_id = uuid.UUID(company_id_str)
                    tenant_id = uuid.UUID(tenant_id_str)
                except ValueError:
                    logger.error(f"Invalid UUID in Stripe metadata for Subscription {sub_stripe.id}.")
                    continue

                # Determinar status y readonly local
                status = "ACTIVE"
                readonly = False
                
                if sub_stripe.status in ["past_due", "unpaid"]:
                    status = "PAST_DUE"
                    readonly = True
                elif sub_stripe.status in ["canceled", "incomplete_expired"]:
                    status = "CANCELED"
                    readonly = True

                # Plan ID Fijo (Enterprise por defecto en recuperación, o extraer de metadata)
                # Para el recovery usamos el Fixed UUID del Forensic Manifest
                default_plan_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
                
                new_sub = Subscription(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    tenant_id=tenant_id,
                    plan_id=default_plan_id,
                    status=status,
                    readonly=readonly,
                    stripe_customer_id=customer.id,
                    stripe_subscription_id=sub_stripe.id,
                    current_storage_usage=0,
                    is_active=True,
                    version_id=1
                )
                
                db.add(new_sub)
                recovered_count += 1

            if recovered_count > 0:
                await db.commit()
                logger.info(f"Stripe Sync Recovery Completed: {recovered_count} subscriptions restored.")
            else:
                logger.info("Stripe Sync Recovery Finished: No matching subscriptions found.")
                
        except Exception as e:
            logger.error(f"Stripe Sync Recovery Failed: {e}")
            await db.rollback()
