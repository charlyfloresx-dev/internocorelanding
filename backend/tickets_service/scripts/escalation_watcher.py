import asyncio
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import SessionLocal
from app.infrastructure.repositories.ticket_repository import SQLAlchemyTicketRepository
from app.infrastructure.repositories.escalation_repository import SQLAlchemyEscalationRepository
from app.services.escalation_service import EscalationConfigService
from app.core.constants import TicketStatus

from common.services.audit_service import AuditService
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("escalation_watcher")

SYSTEM_OPERATOR_HASH = hashlib.sha256(b"SYSTEM_ESCALATION_WATCHER").hexdigest()

class EscalationWatcher:
    """
    Worker que revisa tickets vencidos y aplica la matriz de escalación dinámica.
    """
    
    @classmethod
    async def run(cls):
        logger.info("[START] EscalationWatcher Service is now persistent (Loop: 60s)")
        
        while True:
            try:
                async with SessionLocal() as db:
                    ticket_repo = SQLAlchemyTicketRepository(db)
                    escalation_repo = SQLAlchemyEscalationRepository(db)
                    escalation_service = EscalationConfigService(escalation_repo)
                    
                    # 1. Obtener todos los tickets activos
                    tickets = await ticket_repo.get_tickets_for_escalation()
                    
                    for ticket in tickets:
                        # 2. Obtener reglas de escalación para este ticket
                        area = ticket.area if ticket.area else "_default"
                        rules = await escalation_service.get_escalation_path(ticket.company_id, area)
                        
                        if not rules:
                            continue
                        
                        # 3. Determinar el siguiente nivel de escalación
                        current_level = ticket.escalation_level
                        next_level_rule = next((r for r in rules if r.level == current_level + 1), None)
                        
                        if not next_level_rule:
                            continue
                        
                        # 4. Verificar si el SLA ha expirado (desde creación o nivel anterior)
                        elapsed_minutes = (datetime.now(timezone.utc) - ticket.created_at).total_seconds() / 60
                        
                        if elapsed_minutes >= next_level_rule.sla_minutes:
                            await cls.escalate_ticket(db, ticket_repo, ticket, next_level_rule)
                    
                    await db.commit()
            except Exception as e:
                logger.error(f"Error in watcher loop: {e}")
            
            await asyncio.sleep(60)

    @classmethod
    async def escalate_ticket(cls, db, repo, ticket, rule):
        logger.warning(f"Escalating ticket {ticket.reference_code} to Level {rule.level} ({rule.role_name})")
        
        # Actualizar nivel
        ticket.escalation_level = rule.level
        
        # Agregar comentario de sistema
        system_user_id = UUID("00000000-0000-0000-0000-000000000000")
        await repo.add_comment(
            ticket_id=ticket.id,
            company_id=ticket.company_id,
            content=f"🚨 **ESCALACIÓN AUTOMÁTICA (Nivel {rule.level})**\nSLA Excedido. El ticket ha sido escalado a: **{rule.role_name}**.",
            author_id=system_user_id
        )
        
        # Dispatch Event (Outbox) for Notifications
        from app.schemas.integration_events import TicketStatusChangedEvent
        event = TicketStatusChangedEvent(
            ticket_id=ticket.id,
            company_id=ticket.company_id,
            reference_code=ticket.reference_code,
            title=ticket.title,
            old_status=ticket.status.value,
            new_status=ticket.status.value, # Status no cambia, solo el nivel
            recipient_id=ticket.reported_by_id if ticket.reported_by_id else ticket.created_by,
            changed_by_id=system_user_id,
            metadata={"escalated_to": rule.role_name, "level": rule.level}
        )
        await repo.add_outbox_event(
            company_id=ticket.company_id,
            event_type="TicketEscalatedEvent",
            payload=event.model_dump_json()
        )

        # 🚨 AUDIT TRACE (Industrial Requirement)
        await AuditService.track(
            db=db,
            company_id=ticket.company_id,
            operator_hash=SYSTEM_OPERATOR_HASH,
            action="AUTO_ESCALATION",
            resource="TICKET",
            resource_id=str(ticket.id),
            metadata={
                "reference_code": ticket.reference_code,
                "level": rule.level,
                "role_name": rule.role_name,
                "sla_minutes": rule.sla_minutes
            }
        )

if __name__ == "__main__":
    asyncio.run(EscalationWatcher.run())
