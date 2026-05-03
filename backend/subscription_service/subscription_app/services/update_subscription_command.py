import uuid
from typing import List, Optional
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository
from subscription_app.core.enums import ModuleCode
from common.exceptions import ConflictException, NotFoundException


class UpdateSubscriptionCommand:
    def __init__(self, repo: ISubscriptionRepository, audit_service: Any):
        self.repo = repo
        self.audit_service = audit_service

    async def execute(
        self,
        company_id: uuid.UUID,
        module_codes: List[ModuleCode],
        version_id: int,
        user_id: Optional[uuid.UUID] = None
    ):
        # 1. Obtener suscripción actual con Optimistic Locking
        subscription = await self.repo.get_subscription_by_company_and_version(company_id, version_id)

        if not subscription:
            # Re-check to distinguish between mismatch and not found
            exists = await self.repo.get_subscription_by_company(company_id)
            if exists:
                raise ConflictException(message="Concurrency error: Subscription version mismatch.")
            raise NotFoundException(entity="Subscription", entity_id=str(company_id))

        # 2. Obtener estado previo para auditoría
        old_entitlements = await self.repo.get_entitlements_by_company(company_id)
        before_state = {
            "version": version_id,
            "modules": [e.module_code for e in old_entitlements if e.is_enabled]
        }

        # 3. Validación: No eliminar módulos con usuarios activos
        to_remove = set(before_state["modules"]) - set(module_codes)
        for mod_code in to_remove:
            if await self.repo.check_active_users_for_module(company_id, mod_code):
                raise ConflictException(message=f"No se puede remover el módulo {mod_code} porque tiene usuarios activos.")

        # 4. Actualizar Entitlements
        # Usamos upsert_entitlement para cada módulo mencionado y desactivamos los que no están
        all_potential_modules = set(before_state["modules"]) | set(module_codes)
        for code in all_potential_modules:
            is_enabled = code in module_codes
            await self.repo.upsert_entitlement(company_id, code, is_enabled, subscription.id)

        # 5. Incrementar versión (Optimistic Locking)
        subscription.version_id += 1
        # No hace falta llamar a db.add() si el objeto viene de la sesión y modificamos atributos,
        # pero el repo se encarga del flush/commit al final si es necesario.
        # En una arquitectura limpia purista, deberíamos tener un repo.save(subscription).
        
        # 6. Auditoría
        after_state = {
            "version": subscription.version_id,
            "modules": module_codes
        }
        await self.audit_service.log_change(
            company_id=company_id,
            subscription_id=subscription.id,
            event_type="SUBSCRIPTION_UPDATED",
            before_state=before_state,
            after_state=after_state,
            reason="UpdateSubscriptionCommand execution",
            user_id=user_id
        )

        return subscription
