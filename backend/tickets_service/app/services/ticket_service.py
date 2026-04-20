import uuid
import hashlib
from typing import List, Optional, Tuple
from app.domain.ports.ticket_repository import ITicketRepository
from app.schemas.ticket_dto import TicketCreate, TicketUpdate, TicketCommentCreate
from app.core.constants import TicketStatus, TicketPriority


class TicketService:
    """
    Capa de aplicación para lógica de tickets.
    SOLO depende de ITicketRepository — sin AsyncSession, sin ORM directo.
    El repositorio maneja flush/commit; el servicio solo orquesta la lógica de negocio.
    """

    def __init__(self, repo: ITicketRepository):
        self.repo = repo

    async def create_ticket(self, cmd: TicketCreate, user_id: uuid.UUID) -> "Ticket":  # noqa: F821
        data = {
            "title": cmd.title,
            "description": cmd.description,
            "ticket_type": cmd.ticket_type,
            "priority": cmd.priority,
            "status": TicketStatus.NEW,
            "company_id": cmd.company_id,
            "tenant_id": cmd.company_id,
            "created_by": user_id,
        }
        return await self.repo.create(data)

    async def create_internal_ticket_with_debouncing(
        self,
        cmd: "InternalTicketCreate",  # noqa: F821
        company_id: uuid.UUID
    ) -> Tuple["Ticket", bool]:  # noqa: F821
        """
        Crea un ticket interno con SHA256 Debouncing (Anti-Fatigue).
        Retorna (Ticket, es_nuevo).
        """
        hash_seed = f"{company_id}_{cmd.warehouse_id}_{cmd.product_id}_{cmd.priority.value}"
        dedup_hash = hashlib.sha256(hash_seed.encode()).hexdigest()

        existing = await self.repo.get_by_dedup_hash(dedup_hash, company_id)
        if existing:
            return existing, False

        system_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        data = {
            "title": cmd.title,
            "description": (
                f"[{cmd.source_service}]\n"
                f"Product: {cmd.product_id}\n"
                f"Warehouse: {cmd.warehouse_id}\n"
                f"Details: {cmd.description}\n"
                f"Meta: {cmd.metadata}"
            ),
            "ticket_type": cmd.ticket_type,
            "priority": cmd.priority,
            "status": TicketStatus.NEW,
            "company_id": company_id,
            "tenant_id": company_id,
            "created_by": system_user_id,
            "deduplication_hash": dedup_hash,
        }

        ticket = await self.repo.create(data)

        # Outbox Pattern — entrega garantizada de evento de integración
        import json
        from app.schemas.integration_events import TicketCreatedEvent
        event = TicketCreatedEvent(
            ticket_id=ticket.id,
            company_id=ticket.company_id,
            reference_code=ticket.reference_code,
            title=ticket.title,
            ticket_type=ticket.ticket_type.value,
            priority=ticket.priority.value,
            created_by_id=ticket.created_by,
        )
        await self.repo.add_outbox_event(
            company_id=company_id,
            event_type=event.event_type,
            payload=event.model_dump_json()
        )

        return ticket, True

    async def get_tickets(self, company_id: uuid.UUID) -> List["Ticket"]:  # noqa: F821
        return await self.repo.list_by_company(company_id)

    async def get_ticket(self, ticket_id: uuid.UUID, company_id: uuid.UUID) -> Optional["Ticket"]:  # noqa: F821
        return await self.repo.get_by_id(ticket_id, company_id)

    async def update_ticket(
        self,
        ticket_id: uuid.UUID,
        company_id: uuid.UUID,
        cmd: TicketUpdate,
        user_id: uuid.UUID
    ) -> Optional["Ticket"]:  # noqa: F821
        ticket = await self.repo.get_by_id(ticket_id, company_id)
        if not ticket:
            return None

        updates = {}

        if cmd.status and cmd.status != ticket.status:
            await self.repo.add_history_entry(
                ticket_id=ticket_id,
                change_type="status_change",
                old_value=ticket.status.value,
                new_value=cmd.status.value,
                changed_by_id=user_id
            )
            updates["status"] = cmd.status

        if cmd.priority and cmd.priority != ticket.priority:
            await self.repo.add_history_entry(
                ticket_id=ticket_id,
                change_type="priority_change",
                old_value=ticket.priority.value,
                new_value=cmd.priority.value,
                changed_by_id=user_id
            )
            updates["priority"] = cmd.priority

        if cmd.assigned_to_id and cmd.assigned_to_id != ticket.assigned_to_id:
            await self.repo.add_history_entry(
                ticket_id=ticket_id,
                change_type="assignment_change",
                old_value=str(ticket.assigned_to_id) if ticket.assigned_to_id else None,
                new_value=str(cmd.assigned_to_id),
                changed_by_id=user_id
            )
            updates["assigned_to_id"] = cmd.assigned_to_id

        if cmd.title:
            updates["title"] = cmd.title
        if cmd.description:
            updates["description"] = cmd.description

        return await self.repo.update(ticket_id, company_id, updates)

    async def add_comment(self, cmd: TicketCommentCreate, user_id: uuid.UUID) -> "TicketComment":  # noqa: F821
        return await self.repo.add_comment(
            ticket_id=cmd.ticket_id,
            company_id=cmd.company_id,
            content=cmd.content,
            author_id=user_id,
        )

    async def soft_delete_ticket(
        self,
        ticket_id: uuid.UUID,
        company_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional["Ticket"]:  # noqa: F821
        ticket = await self.repo.get_by_id(ticket_id, company_id)
        if not ticket:
            return None

        await self.repo.add_history_entry(
            ticket_id=ticket_id,
            change_type="soft_delete",
            old_value="active",
            new_value="deleted",
            changed_by_id=user_id
        )

        return await self.repo.soft_delete(ticket_id, company_id)
