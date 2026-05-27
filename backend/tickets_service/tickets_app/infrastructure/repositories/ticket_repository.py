from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
import uuid

from sqlalchemy import select, func, and_, update, delete, or_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from tickets_app.domain.ports.ticket_repository import ITicketRepository
from tickets_app.models.ticket import Ticket
from tickets_app.models.history import TicketHistory
from tickets_app.models.comments import TicketComment
from tickets_app.models.outbox import OutboxEvent
from tickets_app.models.assignee import TicketAssignee
from tickets_app.core.constants import TicketStatus, TicketPriority, TicketType


class SQLAlchemyTicketRepository(ITicketRepository):
    """
    Implementación SQLAlchemy de ITicketRepository.
    Esta clase es la ÚNICA autorizada a usar AsyncSession, select(), flush() y commit().
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _generate_ref_code(self, company_id: UUID) -> str:
        """Genera el folio TKT-YYYY-NNNN único por empresa. Resiliente a colisiones."""
        current_year = datetime.now().year
        # Count all tickets for this company and year, supporting various prefixes (like IT-, SEC-, EXT-, TKT-)
        pattern = f"%-{current_year}-%"
        stmt = select(func.count(Ticket.id)).where(
            Ticket.company_id == company_id,
            Ticket.reference_code.like(pattern)
        )
        result = await self._session.execute(stmt)
        count = result.scalar() or 0
        
        ref = f"TKT-{current_year}-{count + 1:04d}"
        # Verify it doesn't exist for this company
        check = select(func.count(Ticket.id)).where(
            Ticket.company_id == company_id,
            Ticket.reference_code == ref
        )
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
            collaborator_id=data.get("collaborator_id"),
            external_contact_id=data.get("external_contact_id"),
            assigned_department_id=data.get("assigned_department_id"),
            station_id=data.get("station_id"),
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
            selectinload(Ticket.stop_logs),
            selectinload(Ticket.actions),
            selectinload(Ticket.assignees)
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
            selectinload(Ticket.stop_logs),
            selectinload(Ticket.actions),
            selectinload(Ticket.assignees)
        ).where(
            Ticket.company_id == company_id,
            Ticket.is_active == True
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_visibility(
        self,
        company_id: UUID,
        user_id: UUID,
        is_admin: bool,
        is_supervisor: bool,
        department_area: Optional[str] = None,
        department_id: Optional[UUID] = None,
        collaborator_id: Optional[UUID] = None,
        external_contact_id: Optional[UUID] = None,
    ) -> list[Ticket]:
        stmt = select(Ticket).options(
            selectinload(Ticket.comments),
            selectinload(Ticket.history),
            selectinload(Ticket.resources),
            selectinload(Ticket.stop_logs),
            selectinload(Ticket.actions),
            selectinload(Ticket.assignees)
        ).where(
            Ticket.company_id == company_id,
            Ticket.is_active == True
        )

        if not is_admin:
            # INTERNAL identity: legacy direct field + multi-assignee table
            conds = [
                Ticket.assigned_to_id == user_id,
                select(TicketAssignee.id).where(
                    TicketAssignee.ticket_id == Ticket.id,
                    TicketAssignee.company_id == company_id,
                    TicketAssignee.identity_type == 'INTERNAL',
                    TicketAssignee.identity_id == user_id,
                ).exists(),
            ]

            # PLANTA identity (collaborador físico en HCM)
            if collaborator_id:
                conds.append(Ticket.collaborator_id == collaborator_id)
                conds.append(
                    select(TicketAssignee.id).where(
                        TicketAssignee.ticket_id == Ticket.id,
                        TicketAssignee.company_id == company_id,
                        TicketAssignee.identity_type == 'PLANTA',
                        TicketAssignee.identity_id == collaborator_id,
                    ).exists()
                )

            # EXTERNO identity (proveedor / contacto externo)
            if external_contact_id:
                conds.append(Ticket.external_contact_id == external_contact_id)
                conds.append(
                    select(TicketAssignee.id).where(
                        TicketAssignee.ticket_id == Ticket.id,
                        TicketAssignee.company_id == company_id,
                        TicketAssignee.identity_type == 'EXTERNO',
                        TicketAssignee.identity_id == external_contact_id,
                    ).exists()
                )

            if department_area:
                conds.append(Ticket.area == department_area)
            if department_id:
                conds.append(Ticket.assigned_department_id == department_id)

            stmt = stmt.where(or_(*conds))

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
            selectinload(Ticket.stop_logs),
            selectinload(Ticket.actions),
            selectinload(Ticket.assignees)
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

    async def get_by_external_token(self, token: str) -> Optional[Ticket]:
        """Busca ticket por token externo. bypass_tenant: los proveedores
        externos acceden con token opaco sin conocimiento del company_id."""
        stmt = select(Ticket).options(
            selectinload(Ticket.comments),
            selectinload(Ticket.history),
            selectinload(Ticket.resources),
            selectinload(Ticket.stop_logs),
            selectinload(Ticket.actions),
            selectinload(Ticket.assignees)
        ).where(
            Ticket.external_token == token,
            Ticket.is_active == True
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def replace_assignees(
        self,
        ticket_id: UUID,
        company_id: UUID,
        assignees: list,
        assigned_by: UUID,
    ) -> None:
        """Reemplaza todos los ticket_assignees del ticket con la nueva lista."""
        await self._session.execute(
            delete(TicketAssignee).where(
                TicketAssignee.ticket_id == ticket_id,
                TicketAssignee.company_id == company_id,
            )
        )
        now = datetime.now(timezone.utc)
        for a in assignees:
            row = TicketAssignee(
                id=uuid.uuid4(),
                ticket_id=ticket_id,
                company_id=company_id,
                tenant_id=company_id,
                identity_type=a.identity_type,
                identity_id=a.identity_id,
                is_lead=a.is_lead,
                assigned_at=now,
                assigned_by=assigned_by,
                created_by=assigned_by,
            )
            self._session.add(row)
        await self._session.flush()
