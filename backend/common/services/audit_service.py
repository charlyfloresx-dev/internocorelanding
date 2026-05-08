from datetime import datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from common.models.audit import AuditLog
import uuid

class AuditService:
    """Servicio de Auditoría para Interno Core"""
    
    @staticmethod
    async def log_action(
        db: AsyncSession, 
        user_id: Any, 
        action: str, 
        entity_name: str, 
        entity_id: Any, 
        details: Optional[str] = None,
        company_id: Optional[uuid.UUID] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        collaborator_id: Optional[uuid.UUID] = None,
        external_contact_id: Optional[uuid.UUID] = None
    ):
        """Registra una acción en el ledger de auditoría."""
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=str(user_id) if user_id else "SYSTEM",
            action=action,
            table_name=entity_name,
            record_id=str(entity_id) if entity_id else None,
            company_id=company_id,
            tenant_id=company_id,
            old_value=old_value,
            new_value=new_value,
            collaborator_id=collaborator_id,
            external_contact_id=external_contact_id,
            timestamp=datetime.now()
        )
        db.add(log)
        await db.flush() # Ensure it's part of the current transaction
        print(f"[{datetime.now()}] AUDIT_SAVED: User {user_id} - {action} on {entity_name} ({entity_id})")
        return True

    @staticmethod
    async def track(user_id: Any, action: str, resource: str, metadata: dict):
        # Para compatibilidad con codigo que no tiene DB session a la mano (background/fire-and-forget)
        # Por ahora logueamos a consola, pero idealmente usariamos un background_task con un nuevo session_factory
        print(f"[{datetime.now()}] AUDIT_ASYNC_TRACK (TODO_DB): User {user_id} - {action} on {resource} with meta: {metadata}")
        return True