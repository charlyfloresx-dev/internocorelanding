from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
import uuid

from sqlalchemy import select, func, and_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tickets_app.domain.ports.ticket_repository import ITicketRepository
from tickets_app.models.ticket import Ticket
from tickets_app.models.history import TicketHistory
from tickets_app.models.comments import TicketComment
from tickets_app.models.outbox import OutboxEvent
from tickets_app.core.constants import TicketStatus, TicketPriority, TicketType


class SQLAlchemyTicketRepository(ITicketRepository):
    """
    Implementación SQLAlchemy de ITicketRepository.
    Esta clase es la ÚNICA autorizada a usar AsyncSession, select(), flush() y commit().
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _generate_ref_code(self, company_id: UUID) -> str:
        """Genera el folio TKT-YYYY-NNNN globalmente único. Resiliente a colisiones."""
        current_year = datetime.now().year
        pattern = f"TKT-{current_year}-%"
        # Count ALL tickets globally for this year (constraint is global, not per-company)
        stmt = select(func.count(Ticket.id)).where(
            Ticket.reference_code.like(pattern)
        )
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        # Add uuid suffix for extra uniqueness in case of race conditions
        ref = f"TKT-{current_year}-{count + 1:04d}"
        # Verify it doesn't exist
        check = select(func.count(Ticket.id)).where(Ticket.reference_code == ref)
        exists = (await self._session.execute(check)).scalar() or 0
        if exists > 0:
            # Fallback: use timestamp-based suffix
            import time
            ref = f"TKT-{current_year}-{int(time.time()) % 100000:05d}"
        return ref

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

    async def list_by_visibility(
        self, company_id: UUID, user_id: UUID, is_admin: bool, is_supervisor: bool, department_area: Optional[str] = None
    ) -> list[Ticket]:
        stmt = select(Ticket).options(
            selectinload(Ticket.comments),
            selectinload(Ticket.history),
            selectinload(Ticket.resources),
            selectinload(Ticket.stop_logs)
        ).where(
            Ticket.company_id == company_id,
            Ticket.is_active == True
        )
        
        if not is_admin:
            if is_supervisor:
                if department_area:
                    stmt = stmt.where(
                        (Ticket.area == department_area) | 
                        (Ticket.created_by == user_id) | 
                        (Ticket.assigned_to_id == user_id)
                    )
                else:
                    stmt = stmt.where(
                        (Ticket.created_by == user_id) | 
                        (Ticket.assigned_to_id == user_id)
                    )
            else:
                stmt = stmt.where(
                    (Ticket.created_by == user_id) | 
                    (Ticket.assigned_to_id == user_id)
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
        # DEBOUNCING (Evitar Tormentas de Eventos)
        # Verificamos si existe un evento idéntico en los últimos 10 segundos
        debounce_window = datetime.now(timezone.utc) - timedelta(seconds=10)
        
        stmt = select(OutboxEvent).where(
            OutboxEvent.company_id == company_id,
            OutboxEvent.event_type == event_type,
            OutboxEvent.payload == payload,
            OutboxEvent.created_at >= debounce_window
        ).order_by(OutboxEvent.created_at.desc()).limit(1)
        
        recent_event = await self._session.execute(stmt)
        if recent_event.scalar_one_or_none():
            # Ya existe un evento reciente idéntico, ignoramos para debouncing
            return

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
        return list(result.scalars().all())

    async def get_active_by_station(self, station_id: UUID, company_id: UUID) -> List[Ticket]:
        """Obtiene tickets activos asociados a una estación MES."""
        stmt = select(Ticket).where(
            Ticket.station_id == station_id,
            Ticket.company_id == company_id,
            Ticket.status.in_([TicketStatus.NEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS]),
            Ticket.is_active == True
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_technician_workload(self, company_id: UUID) -> dict:
        """Retorna un mapa de {user_id: count} con la carga de tickets activos."""
        stmt = select(Ticket.assigned_to_id, func.count(Ticket.id)).where(
            Ticket.company_id == company_id,
            Ticket.is_active == True,
            Ticket.status.in_([
                TicketStatus.ASSIGNED, 
                TicketStatus.IN_PROGRESS, 
                TicketStatus.IN_REVIEW, 
                TicketStatus.ON_HOLD
            ])
        ).group_by(Ticket.assigned_to_id)
        
        result = await self._session.execute(stmt)
        # result.all() devuelve una lista de tuplas (user_id, count)
        rows = result.all()
        return {str(row[0]): row[1] for row in rows if row[0]}
