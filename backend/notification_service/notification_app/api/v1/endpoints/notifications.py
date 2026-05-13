from typing import List, Optional
from datetime import datetime, timezone
import uuid
import logging
from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from common.responses import ApiResponse
from common.infrastructure.database import get_db
from common.security.dependencies import require_scope
from common.security.auth_payload import TokenPayload
from notification_app.models.notification import Notification, NotificationRecipient
from notification_app.core.websocket import manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=ApiResponse)
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: TokenPayload = Depends(require_scope(["notification:read"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista las notificaciones del usuario actual.
    Cruza la tabla central con los Recipients para el estado is_read.
    """
    query = (
        select(Notification, NotificationRecipient.is_read)
        .join(NotificationRecipient, Notification.id == NotificationRecipient.notification_id)
        .where(
            NotificationRecipient.company_id == current_user.company_id,
            NotificationRecipient.user_id == uuid.UUID(current_user.sub)
        )
    )

    if unread_only:
        query = query.where(NotificationRecipient.is_read == False)

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    data = []
    for notification, is_read in rows:
        n_dict = notification.to_dict()
        n_dict["is_read"] = is_read
        data.append(n_dict)
    
    return ApiResponse(status="success", data=data)

@router.patch("/{notification_id}/read", response_model=ApiResponse)
async def mark_as_read(
    notification_id: uuid.UUID,
    current_user: TokenPayload = Depends(require_scope(["notification:read"])),
    db: AsyncSession = Depends(get_db)
):
    """ Marca una notificación específica como leída. """
    stmt = (
        update(NotificationRecipient)
        .where(
            NotificationRecipient.notification_id == notification_id,
            NotificationRecipient.user_id == uuid.UUID(current_user.sub)
        )
        .values(is_read=True, read_at=datetime.now(timezone.utc))
    )
    res = await db.execute(stmt)
    await db.commit()
    
    logger.info(f"🔔 Notification {notification_id} marked as read for user {current_user.sub}. Rows affected: {res.rowcount}")
    
    return ApiResponse(status="success", message="Notification marked as read")

# ─── WEBSOCKET ENTRYPOINT ──────────────────────────────────────────────────

@router.websocket("/ws/{company_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    company_id: str,
    user_id: str
):
    await manager.connect(websocket, company_id, user_id)
    try:
        while True:
            # Mantener conexión viva y recibir posibles ACKs del cliente
            data = await websocket.receive_text()
            # Podríamos implementar latidos (heartbeats) aquí
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        manager.disconnect(websocket, company_id, user_id)
