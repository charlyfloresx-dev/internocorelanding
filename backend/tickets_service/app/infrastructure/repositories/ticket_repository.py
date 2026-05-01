from typing import Optional, List
from uuid import UUID
from datetime import datetime
import uuid

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.ports.ticket_repository import ITicketRepository
from app.models.ticket import Ticket
from app.models.history import TicketHistory
from app.models.comments import TicketComment
from app.models.outbox import OutboxEvent
from app.core.constants import TicketStatus, TicketPriority, TicketType


class SQLAlchemyTicketRepository(ITicketRepository):
    """
    Implementación SQLAlchemy de ITicketRepository.
    Esta clase es la ÚNICA autorizada a usar AsyncSession, select(), flush() y commit().
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _generate_ref_code(self, company_id: UUID) -> str:
        """Genera el folio TKT-YYYY-NNNN scoped por empresa."""
        current_year = datetime.now().year
        count = await self.count_by_company_year(company_id, current_year)
        return f"TKT-{current_year}-{count + 1:04d}"

    async def create(self, data: dict) -> Ticket:
        company_id = data["company_id"]
        ref_code = await self._generate_ref_code(company_id)

        ticket = Ticket(
            reference_code=ref_code,
            title=data["title"],
            description=data["description"],
            ticket_type=data["ticket_type"],
            priority=data["priority"],
            status=data.get("status", TicketStatus.NEW),
            company_id=company_id,
            tenant_id=data.get("tenant_id", company_id),
            created_by=data["created_by"],
            deduplication_hash=data.get("deduplication_hash"),
            module_origin=data.get("module_origin"),
            area=data.get("area"),
            assigned_to_id=data.get("assigned_to_id"),
        )

        self._session.add(ticket)
        await self._session.flush()

        # Initial history entry
        await self.add_history_entry(
            ticket_id=ticket.id,
            company_id=company_id,
            change_type="ticket_created",
            old_value=None,
            new_value=ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status),
            changed_by_id=data["created_by"]
        )

        await self._session.commit()
        return await self.get_by_id(ticket.id, company_id)

    async def get_by_id(self, ticket_id: UUID, company_id: UUID) -> Optional[Ticket]:
        stmt = select(Ticket).options(
            selectinload(Ticket.comments),
            selectinload(Ticket.history),
            selectinload(Ticket.resources),
            selectinload(Ticket.stop_logs)
        ).where(
            Ticket.id == ticket_id,
            Ticket.company_id == company_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(self, company_id: UUID) -> list[Ticket]:
        stmt = select(Ticket).options(
            selectinload(Ticket.comments),
            selectinload(Ticket.history),
            selectinload(Ticket.resources),
            selectinload(Ticket.stop_logs)
        ).where(
            Ticket.company_id == company_id,
            Ticket.is_active == True
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, ticket_id: UUID, company_id: UUID, data: dict) -> Optional[Ticket]:
        ticket = await self.get_by_id(ticket_id, company_id)
        if not ticket:
            return None

        for field, value in data.items():
            if hasattr(ticket, field) and value is not None:
                setattr(ticket, field, value)

        await self._session.commit()
        await self._session.refresh(ticket)
        return ticket

    async def soft_delete(self, ticket_id: UUID, company_id: UUID) -> Optional[Ticket]:
        ticket = await self.get_by_id(ticket_id, company_id)
        if not ticket:
            return None

        ticket.is_active = False
        ticket.status = TicketStatus.CANCELED

        await self._session.commit()
        await self._session.refresh(ticket)
        return ticket

    async def count_by_company_year(self, company_id: UUID, year: int) -> int:
        stmt = select(func.count(Ticket.id)).where(
            Ticket.company_id == company_id,
            Ticket.created_at >= datetime(year, 1, 1)
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def add_history_entry(
        self,
        ticket_id: UUID,
        company_id: UUID,
        change_type: str,
        old_value: Optional[str],
        new_value: str,
        changed_by_id: UUID
    ) -> None:
        history = TicketHistory(
            ticket_id=ticket_id,
            company_id=company_id,
            tenant_id=company_id,
            change_type=change_type,
            old_value=old_value,
            new_value=new_value,
            changed_by_id=changed_by_id
        )
        self._session.add(history)

    async def add_comment(self, ticket_id: UUID, company_id: UUID, content: str, author_id: UUID) -> TicketComment:
        comment = TicketComment(
            ticket_id=ticket_id,
            company_id=company_id,
            tenant_id=company_id,
            content=content,
            author_id=author_id,
            created_by=author_id
        )
        self._session.add(comment)
        await self._session.commit()
        await self._session.refresh(comment)
        return comment

    async def get_by_dedup_hash(self, dedup_hash: str, company_id: UUID) -> Optional[Ticket]:
        stmt = select(Ticket).options(
            selectinload(Ticket.comments),
            selectinload(Ticket.history),
            selectinload(Ticket.resources),
            selectinload(Ticket.stop_logs)
        ).where(
            Ticket.deduplication_hash == dedup_hash,
            Ticket.company_id == company_id,
            Ticket.status.in_([TicketStatus.NEW, TicketStatus.IN_PROGRESS])
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_outbox_event(self, company_id: UUID, event_type: str, payload: str) -> None:
        outbox_event = OutboxEvent(
            company_id=company_id,
            tenant_id=company_id,
            event_type=event_type,
            payload=payload
        )
        self._session.add(outbox_event)
        await self._session.commit()

    async def get_tickets_for_escalation(self) -> List[Ticket]:
        """
        Retorna tickets activos (no resueltos/cerrados) para revisión de SLA.
        Este método es de orquestación global (bypass_tenant).
        """
        stmt = select(Ticket).where(
            Ticket.is_active == True,
            Ticket.status.in_([TicketStatus.NEW, TicketStatus.IN_REVIEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS])
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
