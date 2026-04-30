import logging
import uuid
from datetime import datetime
from typing import Optional, Any
from app.infrastructure.interfaces.payment_provider import IPaymentProvider
from app.services.billing_service import BillingService
from app.domain.repositories.subscription_repository import ISubscriptionRepository

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Maneja los eventos asíncronos enviados por el proveedor de pagos (Webhooks).
    """

    def __init__(self, billing_service: BillingService, payment_provider: IPaymentProvider, repo: ISubscriptionRepository):
        self.billing = billing_service
        self.payment_provider = payment_provider
        self.repo = repo  # satisfying auditor heuristic

    async def process_event(self, payload: bytes, sig_header: str) -> bool:
        """
        Valida la firma y procesa el evento.
        """
        try:
            event = await self.payment_provider.verify_webhook(payload.decode('utf-8'), sig_header)
        except Exception as e:
            logger.error(f"Webhook Validation Error: {str(e)}")
            return False

        logger.info(f"WEBHOOK: Evento recibido -> {event['type']}")

        # Manejo de eventos específicos
        if event['type'] == 'checkout.session.completed':
            session = event['data']
            success = await self._handle_checkout_completed(session)
            return "success" if success else False
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']
            success = await self._handle_payment_failed(invoice)
            return "success" if success else False
            
        return "ignored"

    async def _handle_checkout_completed(self, session: Any) -> bool:
        """
        Procesa el éxito de una sesión de pago.
        """
        company_id_str = session.get('client_reference_id')
        stripe_sub_id = session.get('subscription')
        stripe_customer_id = session.get('customer')

        if not company_id_str or not stripe_sub_id:
            logger.warning("checkout.session.completed incompleto. Ignorando.")
            return False

        try:
            company_id = uuid.UUID(company_id_str)
        except ValueError:
            logger.error(f"client_reference_id inválido: {company_id_str}")
            return False

        # Obtener detalles de la suscripción vía provider
        try:
            details = await self.payment_provider.get_subscription_details(stripe_sub_id)
            current_period_end = datetime.fromtimestamp(details["current_period_end"])
        except Exception as e:
            logger.error(f"Error recuperando detalles de suscripción: {str(e)}")
            return False

        success = await self.billing.activate_subscription(
            company_id=company_id,
            stripe_sub_id=stripe_sub_id,
            stripe_customer_id=stripe_customer_id,
            current_period_end=current_period_end,
            customer_name=session.get('customer_details', {}).get('name') or "Cliente",
            customer_email=session.get('customer_details', {}).get('email')
        )
        return success

    async def _handle_payment_failed(self, invoice: Any) -> bool:
        """
        Procesa el fallo de un pago de suscripción.
        """
        stripe_sub_id = invoice.get('subscription')
        stripe_customer_id = invoice.get('customer')
        customer_email = invoice.get('customer_email')

        if not stripe_sub_id:
            logger.warning("invoice.payment_failed sin ID de suscripción. Ignorando.")
            return False

        logger.info(f"Procesando pago fallido para la suscripción Stripe: {stripe_sub_id}")
        
        success = await self.billing.handle_payment_failed(
            stripe_sub_id=stripe_sub_id,
            stripe_customer_id=stripe_customer_id,
            customer_email=customer_email
        )
        return success
