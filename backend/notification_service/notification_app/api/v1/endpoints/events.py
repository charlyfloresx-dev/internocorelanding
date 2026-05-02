from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

from common.responses import ApiResponse
from common.infrastructure.database import get_db
from notification_app.models.notification import Notification, NotificationRecipient
# ProcessedEvent might be in another model file, let's check.
# For now, I'll skip idempotency if I can't find ProcessedEvent or just import it if it exists.
try:
    from notification_app.models.event_log import ProcessedEvent
except ImportError:
    ProcessedEvent = None

router = APIRouter(tags=["Integration: Events"])
logger = logging.getLogger("notification.event_consumer")

@router.post("/events", response_model=ApiResponse, status_code=202)
async def consume_event(
    payload: dict,
    x_company_id: uuid.UUID = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Idempotent Event Consumer.
    Receives HTTP POSTs from the tickets_service OutboxWorker.
    """
    event_id = payload.get("event_id")
    event_type = payload.get("event_type")

    logger.info(f"Received {event_type} [{event_id}] for Company {x_company_id}")

    # ── Idempotency Guard ──────────────────────────────────────────────────────
    if event_id and ProcessedEvent:
        existing = await db.execute(
            select(ProcessedEvent).where(ProcessedEvent.event_id == event_id).limit(1)
        )
        if existing.scalar_one_or_none():
            logger.info(f"[IDEMPOTENCY] Event [{event_id}] already handled.")
            return ApiResponse(message="Event already handled", data={"event_id": event_id})

        # Mark as processed
        db.add(ProcessedEvent(
            event_id=event_id, 
            event_type=event_type, 
            company_id=x_company_id
        ))

    # ── Dispatch: TicketCreatedEvent ───────────────────────────────────────────
    if event_type == "TicketCreatedEvent":
        ticket_id = payload.get("ticket_id")
        priority = payload.get("priority", "LOW")
        description = payload.get("description", "Ticket created")
        assigned_user_id = payload.get("assigned_to_id")

        # Simplified dispatch: just create an in-app notification for now
        notification = Notification(
            company_id=x_company_id,
            tenant_id=x_company_id,
            type="TicketCreated",
            title=f"Ticket {ticket_id} created",
            message=description,
            priority=priority if priority in ["CRITICAL","HIGH","MEDIUM","LOW"] else "MEDIUM",
            status="SENT",
        )
        db.add(notification)
        await db.flush()

        if assigned_user_id:
            db.add(NotificationRecipient(
                notification_id=notification.id,
                user_id=uuid.UUID(assigned_user_id) if isinstance(assigned_user_id, str) else assigned_user_id,
                company_id=x_company_id,
                tenant_id=x_company_id,
                is_read=False,
            ))
        
        await db.commit()
        logger.info(f"Notification created for ticket {ticket_id}")

    return ApiResponse(message="Event Accepted", data={"event_id": event_id})
