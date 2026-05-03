import uuid
from typing import Optional
from subscription_app.domain.repositories.subscription_repository import ISubscriptionRepository


class AuditService:
    def __init__(self, repo: ISubscriptionRepository):
        self.repo = repo

    async def log_change(
        self,
        company_id: uuid.UUID,
        subscription_id: uuid.UUID,
        event_type: str,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        reason: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        user_ip: Optional[str] = None
    ):
        """
        Registra un cambio inmutable en el log de auditoría de suscripciones.
        """
        if user_ip and after_state:
            after_state["_audit_info"] = {"ip": user_ip}

        audit_data = {
            "company_id": company_id,
            "subscription_id": subscription_id,
            "event_type": event_type,
            "before_state": before_state,
            "after_state": after_state,
            "reason": reason,
            "created_by": user_id
        }

        await self.repo.save_audit_log(audit_data)
