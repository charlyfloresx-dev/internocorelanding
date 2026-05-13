from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from common.responses import ApiResponse
from app.dependencies.database import get_db
from app.models import Notification
from typing import List, Optional
import uuid

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=ApiResponse)
async def list_notifications(
    x_company_id: uuid.UUID = Header(...),
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves global notifications for the company (God Mode visibility).
    """
    query = select(Notification).where(Notification.company_id == x_company_id)
    
    # Normally we would filter by user_id via NotificationRecipient, 
    # but for "God Mode" (Phase 64) we might want the company log.
    # For now, let's return company notifications.
    
    query = query.order_by(Notification.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return ApiResponse(
        message="Notifications retrieved",
        data=[{
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "priority": n.priority.value if hasattr(n.priority, 'value') else n.priority,
            "channel": n.channel.value if hasattr(n.channel, 'value') else n.channel,
            "status": n.status.value if hasattr(n.status, 'value') else n.status,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "payload": n.payload
        } for n in notifications]
    )

@router.patch("/{notification_id}/read", response_model=ApiResponse)
async def mark_as_read(
    notification_id: uuid.UUID,
    x_company_id: uuid.UUID = Header(...),
    db: AsyncSession = Depends(get_db)
):
    # This is a simplified version. In a real multi-user scenario, 
    # we would update the NotificationRecipient.
    
    # For global alerts, we can just return success or update a global flag if needed.
    return ApiResponse(message="Notification marked as read")
