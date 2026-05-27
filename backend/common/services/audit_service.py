from datetime import datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from common.models.audit import AuditLog
import uuid
import logging

_logger = logging.getLogger(__name__)

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
        external_contact_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
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
            client_ip=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(),
        )
        db.add(log)
        await db.flush()
        return True

    @staticmethod
    async def track(user_id: Any, action: str, resource: str, metadata: dict):
        import asyncio

        async def _persist():
            try:
                from common.infrastructure.database import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        await AuditService.log_action(
                            db=session,
                            user_id=user_id,
                            action=action,
                            entity_name=resource,
                            entity_id=metadata.get("trace_id"),
                            details=str(metadata),
                        )
            except Exception as exc:
                _logger.warning(f"AuditService.track DB persist failed: {exc}")

        asyncio.create_task(_persist())
        return True