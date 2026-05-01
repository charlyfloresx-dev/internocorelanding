from datetime import datetime
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

class AuditService:
    """Servicio de Auditoría para Interno Core"""
    
    @staticmethod
    async def log_action(
        db: AsyncSession, 
        user_id: Any, 
        action: str, 
        entity_name: str, 
        entity_id: Any, 
        details: Optional[str] = None
    ):
        # Por ahora solo imprimimos en consola para validar que funciona
        # En el futuro, esto insertará en la tabla audit_logs
        print(f"[{datetime.now()}] AUDIT: User {user_id} - {action} on {entity_name} ({entity_id})")
        return True

    @staticmethod
    async def track(user_id: Any, action: str, resource: str, metadata: dict):
        print(f"[{datetime.now()}] AUDIT TRACK: User {user_id} - {action} on {resource} with meta: {metadata}")
        return True