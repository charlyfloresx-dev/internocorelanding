from typing import List, Optional
import uuid
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from common.infrastructure.database import get_db
from common.responses import ApiResponse
from common.models.audit import AuditLog
from common.security.auth_payload import TokenPayload
from common.security.dependencies import require_scope, get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=ApiResponse, dependencies=[Depends(require_scope(["inventory:read"]))])
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    token: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Security: require_scope handled in decorator
    """
    Lista los registros de auditoría para la empresa actual.
    """
    query = select(AuditLog).where(AuditLog.company_id == token.company_id)
    
    if table_name:
        query = query.where(AuditLog.table_name == table_name)
    if action:
        query = query.where(AuditLog.action == action)
        
    query = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Transform to dict for serialization
    data = []
    for log in logs:
        data.append({
            "id": str(log.id),
            "action": log.action,
            "table_name": log.table_name,
            "record_id": log.record_id,
            "user_id": log.user_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "trace_id": str(log.correlation_id) if log.correlation_id else None
        })
        
    return ApiResponse(status="success", data=data)
