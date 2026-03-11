from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from common.schemas import ApiResponse
from app.db.session import get_db
from app.models import Notification, NotificationRecipient
from app.models.event_log import ProcessedEvent
from app.services.preference_service import PreferenceService
from app.services.providers import get_provider
from app.services.template_service import TemplateService
import uuid
import logging

logger = logging.getLogger("notification.event_consumer")
router = APIRouter(prefix="/events", tags=["integration-events"])

# Global instance for efficiency
template_service = TemplateService()


@router.post("/", response_model=ApiResponse, status_code=202)
async def consume_event(
    payload: dict,
    x_company_id: uuid.UUID = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Idempotent Event Consumer.
    Receives HTTP POSTs from the tickets_service OutboxWorker.
    Skips processing if event_id was already handled (idempotency guard).
    """
    event_id = payload.get("event_id")
    event_type = payload.get("event_type")

    logger.info(f"Received {event_type} [{event_id}] for Company {x_company_id}")

    # ── Idempotency Guard ──────────────────────────────────────────────────────
    if event_id:
        existing = await db.execute(
            select(ProcessedEvent).where(ProcessedEvent.event_id == event_id).limit(1)
        )
        if existing.scalar_one_or_none():
            logger.info(f"[IDEMPOTENCY] Event [{event_id}] already handled.")
            return ApiResponse(message="Event already handled", data={"event_id": event_id})

        # Mark as processed immediately (In this transaction)
        db.add(ProcessedEvent(event_id=event_id, event_type=event_type))

    # ── Dispatch: TicketCreatedEvent ───────────────────────────────────────────
    if event_type == "TicketCreatedEvent":
        ticket_id = payload.get("ticket_id")
        priority = payload.get("priority", "LOW")
        description = payload.get("description", "Ticket created")
        assigned_user_id = payload.get("assigned_to_id")

        channels = await PreferenceService(db).get_user_channels(
            user_id=assigned_user_id,
            company_id=x_company_id,
            priority=priority,
        )

        for channel in channels:
            notification = Notification(
                company_id=x_company_id,
                event_id=event_id,        # stored to enable idempotency lookup
                type="TicketCreated",
                title=f"Ticket {ticket_id} created",
                message=description,
                priority=priority,
                channel=channel,
                status="PENDING",
            )
            db.add(notification)
            await db.flush()

            if assigned_user_id:
                db.add(NotificationRecipient(
                    notification_id=notification.id,
                    user_id=assigned_user_id,
                    is_read=False,
                ))

            # ── External Dispatch via BaseProvider ─────────────────────────────
            try:
                provider = get_provider(channel)
                if provider:
                    # Inyectar company_id en metadata para trazabilidad (Requisito 3)
                    dispatch_metadata = {
                        "ticket_id": ticket_id, 
                        "priority": priority,
                        "company_id": x_company_id
                    }
                    
                    message_to_send = notification.message
                    if channel == "EMAIL":
                        message_to_send = template_service.render_notification(
                            content=notification.message,
                            company_id=str(x_company_id)
                        )
                    
                    success = await provider.send(
                        recipient=str(assigned_user_id),
                        title=notification.title,
                        message=message_to_send,
                        metadata=dispatch_metadata,
                    )
                    notification.status = "SENT" if success else "FAILED"
                else:
                    # IN_APP o canal no soportado por provider externo
                    notification.status = "SENT"
            except Exception as exc:
                logger.error(f"Fail-Safe: Provider error for channel {channel}: {str(exc)}")
                notification.status = "FAILED"

            logger.info(
                f"[{channel}] event={event_id} ticket={ticket_id} "
                f"status={notification.status} user={assigned_user_id}"
            )

        await db.commit()

    # ── Dispatch: SubscriptionActivatedEvent ─────────────────────────────────
    if event_type == "SubscriptionActivatedEvent":
        user_name = payload.get("user_name", "Cliente")
        company_name = payload.get("company_name", "Tu Empresa")
        plan_name = payload.get("plan_name", "Plan Pro")
        expiry_date = payload.get("expiry_date", "N/A")
        user_email = payload.get("user_email")

        if not user_email:
            logger.error("SubscriptionActivatedEvent sin user_email. Abortando.")
            return ApiResponse(message="Falta user_email", status_code=400)

        try:
            # 1. Renderizar HTML profesional
            html_content = template_service.render_subscription_success({
                "user_name": user_name,
                "company_name": company_name,
                "plan_name": plan_name,
                "expiry_date": expiry_date
            })

            # 2. Despachar vía Resend
            provider = get_provider("EMAIL")
            if provider:
                success = await provider.send(
                    recipient=user_email,
                    title="🚀 ¡Suscripción Activada - Interno Core!",
                    message=html_content,
                    metadata={"company_id": x_company_id, "event_type": event_type}
                )
                logger.info(f"📧 [SUBS_EMAIL] Despachado a {user_email}. Exito: {success}")
                
            # 3. Registrar notificación en DB para auditoría
            notification = Notification(
                company_id=x_company_id,
                event_id=event_id,
                type="SubscriptionActivated",
                title="Suscripción Activada",
                message=f"Plan {plan_name} activo para {company_name}",
                priority="HIGH",
                channel="EMAIL",
                status="SENT" if success else "FAILED"
            )
            db.add(notification)
            await db.commit()

        except Exception as exc:
            logger.error(f"Error procesando SubscriptionActivatedEvent: {str(exc)}")
            return ApiResponse(message="Error interno", status_code=500)

    return ApiResponse(message="Event Accepted", data={"event_id": event_id})

