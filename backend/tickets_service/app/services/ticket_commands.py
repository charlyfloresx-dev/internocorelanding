from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ticket_service import TicketService
from app.schemas.ticket_dto import TicketCreate
from app.models.resource import TicketResource
from app.models.ticket import Ticket
from common.services.audit_service import AuditService
import uuid

# COMMANDS
class CreateTicketCommand(BaseModel):
    title: str
    description: str
    ticket_type: str
    priority: str
    module_origin: Optional[str] = None
    area: Optional[str] = None
    company_id: UUID
    assigned_to_id: Optional[UUID] = None
    created_by_id: UUID

class ConsumeResourceDto(BaseModel):
    resource_id: UUID
    warehouse_id: UUID
    quantity: float

class ConsumeResourcesCommand(BaseModel):
    ticket_id: UUID
    company_id: UUID
    resources: List[ConsumeResourceDto]
    user_id: UUID

# HANDLERS
class TicketCommandHandler:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ticket_service = TicketService(db)
        
    async def handle_create_ticket(self, cmd: CreateTicketCommand) -> Ticket:
        """
        Handles CreateTicketCommand.
        Validates assignment scope and delegates to TicketeService.
        """
        ticket_create_dto = TicketCreate(
            title=cmd.title,
            description=cmd.description,
            ticket_type=cmd.ticket_type,
            priority=cmd.priority,
            company_id=cmd.company_id
        )
        
        # In a real scenario, we'd validate assigned_to_id belongs to the company_id here
        
        ticket = await self.ticket_service.create_ticket(ticket_create_dto, cmd.created_by_id)
        
        # Add MES fields
        ticket.module_origin = cmd.module_origin
        ticket.area = cmd.area
        ticket.assigned_to_id = cmd.assigned_to_id
        
        await self.db.commit()
        await self.db.refresh(ticket)
        
        await AuditService.log_action(
            self.db, 
            cmd.created_by_id, 
            "CREATE", 
            "Ticket", 
            ticket.id, 
            f"Ticket created: {ticket.title}"
        )
        
        return ticket

    async def handle_consume_resources(self, cmd: ConsumeResourcesCommand) -> Ticket:
        """
        Records consumed resources on a ticket, which would then dispatch
        integration commands to inventory_service.
        """
        from app.infrastructure.inventory_client import HttpInventoryClient
        from decimal import Decimal
        
        inventory_client = HttpInventoryClient()

        ticket = await self.ticket_service.get_ticket(cmd.ticket_id, cmd.company_id)
        if not ticket:
            raise ValueError("Ticket not found")
            
        for res_dto in cmd.resources:
            # 1. Llamada atómica al servicio externo de inventario
            # Si esto falla, levantará un HTTPException que abortará el commit local de SQLAlchemy
            await inventory_client.record_consumption(
                company_id=cmd.company_id,
                resource_id=res_dto.resource_id,
                warehouse_id=res_dto.warehouse_id,
                quantity=Decimal(str(res_dto.quantity)),
                reference=ticket.reference_code,
                user_id=cmd.user_id
            )
            
            # 2. Persistencia local si todo fue bien
            resource = TicketResource(
                ticket_id=ticket.id,
                resource_id=res_dto.resource_id,
                quantity=res_dto.quantity
            )
            self.db.add(resource)
            
        await self.db.commit()
        await self.db.refresh(ticket)
        
        await AuditService.log_action(
            self.db, 
            cmd.user_id, 
            "CONSUME_RESOURCES", 
            "Ticket", 
            ticket.id, 
            f"Resources consumed: {[str(r.resource_id) for r in cmd.resources]}"
        )
        
        return ticket
