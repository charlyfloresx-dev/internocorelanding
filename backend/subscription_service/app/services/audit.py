import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import AuditSubscriptionLog

class AuditService:
    @staticmethod
    async def log_change(
        db: AsyncSession,
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
        log_entry = AuditSubscriptionLog(
            company_id=company_id,
            subscription_id=subscription_id,
            event_type=event_type,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            created_by=user_id,
            transaction_id=uuid.uuid4() # Idealmente vendría del request_context
        )
        # Nota: IP se podría guardar en el campo 'reason' o extender el modelo si fuera crítico,
        # pero por ahora lo incluimos en el after_state o reason para enfoque 'low cost'.
        if user_ip and after_state:
            after_state["_audit_info"] = {"ip": user_ip}

        db.add(log_entry)
        await db.flush() # Guardar sin confirmar para que sea parte de la transacción del comando
