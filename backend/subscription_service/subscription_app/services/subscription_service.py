import uuid
from typing import Dict, Any, Optional
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository
from common.exceptions import BusinessRuleException


class SubscriptionService:
    """
    Servicio central de gobernanza de suscripciones.
    Implementa validaciones de almacenamiento, control de módulos y aislamiento de tenant.
    """

    def __init__(self, repo: ISubscriptionRepository):
        self.repo = repo

    async def get_subscription(self, company_id: uuid.UUID) -> Optional[Any]:
        """Obtiene la suscripción activa de un tenant."""
        return await self.repo.get_subscription_by_company(company_id)

    async def check_storage_limit(self, company_id: uuid.UUID, new_file_size: int):
        """
        Valida que el tenant no exceda su límite de almacenamiento.
        """
        subscription = await self.repo.get_subscription_by_company(company_id)
        if not subscription or not getattr(subscription, 'plan', None):
            raise BusinessRuleException("No se encontró una suscripción activa para validar el almacenamiento.")

        plan = subscription.plan
        current_usage = subscription.current_storage_usage
        limit = getattr(plan, 'storage_limit', 5368709120)  # Default 5GB if not found

        if not getattr(plan, 'allow_overage', False):
            if current_usage + new_file_size > limit:
                raise BusinessRuleException(f"Límite de almacenamiento excedido ({limit} bytes). Operación bloqueada.")
        
        return True

    async def update_usage(self, company_id: uuid.UUID, size_delta: int):
        """Actualiza el uso de almacenamiento cargado al tenant."""
        subscription = await self.repo.get_subscription_by_company(company_id)
        if subscription:
            update_data = {"current_storage_usage": subscription.current_storage_usage + size_delta}
            await self.repo.update_subscription(subscription.stripe_subscription_id, update_data)
