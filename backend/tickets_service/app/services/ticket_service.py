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
        # Generate Reference Code (TKT-YEAR-SEQ)
        current_year = datetime.now().year
        # Count tickets for this year to generate sequence (simplified)
        query = select(func.count(Ticket.id)).where(Ticket.created_at >= datetime(current_year, 1, 1))
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
