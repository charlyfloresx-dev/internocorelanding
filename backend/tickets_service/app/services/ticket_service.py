from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.ticket import Ticket
from app.models.history import TicketHistory
from app.models.comments import TicketComment
from app.schemas.ticket_dto import TicketCreate, TicketUpdate, TicketCommentCreate
from app.core.constants import TicketStatus
from datetime import datetime
import uuid
from typing import List, Optional

class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(self, cmd: TicketCreate, user_id: uuid.UUID) -> Ticket:
        # Generate Reference Code (TKT-YEAR-SEQ) — scoped by company_id for multi-tenant isolation
        current_year = datetime.now().year
        query = select(func.count(Ticket.id)).where(
            Ticket.company_id == cmd.company_id,
            Ticket.created_at >= datetime(current_year, 1, 1)
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        ref_code = f"TKT-{current_year}-{count + 1:04d}"

        new_ticket = Ticket(
            reference_code=ref_code,
            title=cmd.title,
            description=cmd.description,
            ticket_type=cmd.ticket_type,
            priority=cmd.priority,
            status=TicketStatus.NEW,
            company_id=cmd.company_id,
            created_by=user_id
        )
        
        self.db.add(new_ticket)
        await self.db.flush()

        # Initial History Entry
        history = TicketHistory(
            ticket_id=new_ticket.id,
            change_type="ticket_created",
            new_value=TicketStatus.NEW,
            changed_by_id=user_id
        )
        self.db.add(history)
        
        await self.db.commit()
        await self.db.refresh(new_ticket)
        return new_ticket

    async def create_internal_ticket_with_debouncing(self, cmd: "InternalTicketCreate", company_id: uuid.UUID) -> tuple[Ticket, bool]:
        """
        Creates an internal ticket with SHA256 Debouncing (Anti-Fatigue).
        Returns a tuple: (Ticket, is_new_ticket).
        If an OPEN ticket exists with the same hash, it's skipped.
        """
        import hashlib
        from app.schemas.ticket_dto import TicketCreate
        
        # 1. Compute Hash (company_id + warehouse_id + product_id + priority)
        hash_seed = f"{company_id}_{cmd.warehouse_id}_{cmd.product_id}_{cmd.priority.value}"
        dedup_hash = hashlib.sha256(hash_seed.encode()).hexdigest()

        # 2. Check for existing OPEN tickets with this hash
        query = select(Ticket).where(
            Ticket.deduplication_hash == dedup_hash,
            Ticket.company_id == company_id,
            Ticket.status.in_([TicketStatus.NEW, TicketStatus.IN_PROGRESS])
        )
        result = await self.db.execute(query)
        existing_ticket = result.scalar_one_or_none()

        if existing_ticket:
            return existing_ticket, False # Return existing ticket, not a new one

        # 3. Create New Ticket
        # System User ID used for internal system notifications
        system_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        
        # Generate Reference Code (TKT-YEAR-SEQ) — scoped by company_id for multi-tenant isolation
        current_year = datetime.now().year
        query_count = select(func.count(Ticket.id)).where(
            Ticket.company_id == company_id,
            Ticket.created_at >= datetime(current_year, 1, 1)
        )
        result_count = await self.db.execute(query_count)
        count = result_count.scalar() or 0
        ref_code = f"TKT-{current_year}-{count + 1:04d}"

        new_ticket = Ticket(
            reference_code=ref_code,
            title=cmd.title,
            description=f"[{cmd.source_service}]\nProduct: {cmd.product_id}\nWarehouse: {cmd.warehouse_id}\nDetails: {cmd.description}\nMeta: {cmd.metadata}",
            ticket_type=cmd.ticket_type,
            priority=cmd.priority,
            status=TicketStatus.NEW,
            company_id=company_id,
            created_by=system_user_id,
            deduplication_hash=dedup_hash
        )
        
        self.db.add(new_ticket)
        await self.db.flush()

        history = TicketHistory(
            ticket_id=new_ticket.id,
            change_type="system_alert_created",
            new_value=cmd.priority.value,
            changed_by_id=system_user_id
        )
        self.db.add(history)
        
        
        await self.db.commit()
        await self.db.refresh(new_ticket)
        
        # 4. Outbox Pattern: Emit integration event instead of tight coupling
        import json
        from app.schemas.integration_events import TicketCreatedEvent
        from app.models.outbox import OutboxEvent
        
        event_payload = TicketCreatedEvent(
            ticket_id=new_ticket.id,
            company_id=new_ticket.company_id,
            reference_code=new_ticket.reference_code,
            title=new_ticket.title,
            ticket_type=new_ticket.ticket_type.value,
            priority=new_ticket.priority.value,
            created_by_id=new_ticket.created_by
        )
        
        outbox_event = OutboxEvent(
            company_id=new_ticket.company_id,
            event_type=event_payload.event_type,
            payload=event_payload.model_dump_json()
        )
        self.db.add(outbox_event)
        
        # We commit the OutboxEvent in the same transaction
        await self.db.commit()
        
        return new_ticket, True

    async def get_tickets(self, company_id: uuid.UUID) -> List[Ticket]:
        query = select(Ticket).where(Ticket.company_id == company_id).where(Ticket.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_ticket(self, ticket_id: uuid.UUID, company_id: uuid.UUID) -> Optional[Ticket]:
        query = select(Ticket).where(Ticket.id == ticket_id, Ticket.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_ticket(self, ticket_id: uuid.UUID, company_id: uuid.UUID, cmd: TicketUpdate, user_id: uuid.UUID) -> Optional[Ticket]:
        ticket = await self.get_ticket(ticket_id, company_id)
        if not ticket:
            return None

        # Track history for specific fields
        if cmd.status and cmd.status != ticket.status:
            history = TicketHistory(
                ticket_id=ticket.id,
                change_type="status_change",
                old_value=ticket.status.value,
                new_value=cmd.status.value,
                changed_by_id=user_id
            )
            self.db.add(history)
            ticket.status = cmd.status

        if cmd.priority and cmd.priority != ticket.priority:
            history = TicketHistory(
                ticket_id=ticket.id,
                change_type="priority_change",
                old_value=ticket.priority.value,
                new_value=cmd.priority.value,
                changed_by_id=user_id
            )
            self.db.add(history)
            ticket.priority = cmd.priority

        if cmd.assigned_to_id and cmd.assigned_to_id != ticket.assigned_to_id:
            history = TicketHistory(
                ticket_id=ticket.id,
                change_type="assignment_change",
                old_value=str(ticket.assigned_to_id) if ticket.assigned_to_id else None,
                new_value=str(cmd.assigned_to_id),
                changed_by_id=user_id
            )
            self.db.add(history)
            ticket.assigned_to_id = cmd.assigned_to_id

        if cmd.title: ticket.title = cmd.title
        if cmd.description: ticket.description = cmd.description

        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def add_comment(self, cmd: TicketCommentCreate, user_id: uuid.UUID) -> TicketComment:
        comment = TicketComment(
            ticket_id=cmd.ticket_id,
            company_id=cmd.company_id,
            content=cmd.content,
            author_id=user_id,
            created_by=user_id
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def soft_delete_ticket(self, ticket_id: uuid.UUID, company_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Ticket]:
        """
        Soft-delete: marca is_active=False en vez de eliminar el registro.
        Registra el cambio en TicketHistory y dispara AuditService.log_action.
        """
        from common.services.audit_service import AuditService

        ticket = await self.get_ticket(ticket_id, company_id)
        if not ticket:
            return None

        ticket.is_active = False
        ticket.status = TicketStatus.CANCELED

        # History trail
        history = TicketHistory(
            ticket_id=ticket.id,
            change_type="soft_delete",
            old_value="active",
            new_value="deleted",
            changed_by_id=user_id
        )
        self.db.add(history)

        await self.db.commit()
        await self.db.refresh(ticket)

        # Forensic audit
        await AuditService.log_action(
            self.db,
            user_id,
            "SOFT_DELETE",
            "Ticket",
            ticket.id,
            f"Ticket soft-deleted: {ticket.reference_code}"
        )

        return ticket

