from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import uuid

from app.domain.ports.ticket_repository import ITicketRepository
from app.domain.ports.inventory_client import IInventoryClient
from app.services.ticket_service import TicketService
from app.schemas.ticket_dto import TicketCreate
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────

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


# ─────────────────────────────────────────
# HANDLER — Recibe interfaces, no AsyncSession
# ─────────────────────────────────────────

class TicketCommandHandler:
    """
    Orquesta Commands de tickets.
    Depende de ITicketRepository e IInventoryClient — sin AsyncSession ni ORM directo.
    """

    def __init__(self, repo: ITicketRepository, inventory_client: IInventoryClient, audit_repo: Optional[any] = None):
        self.repo = repo
        self.inventory_client = inventory_client
        self.audit_repo = audit_repo
        self._service = TicketService(repo)

    async def handle_create_ticket(self, cmd: CreateTicketCommand) -> "Ticket":  # noqa: F821
        """
        Maneja CreateTicketCommand.
        Valida el scope de asignación y delega al TicketService.
        """
        ticket_create_dto = TicketCreate(
            title=cmd.title,
            description=cmd.description,
            ticket_type=cmd.ticket_type,
            priority=cmd.priority,
            company_id=cmd.company_id
        )

        ticket = await self._service.create_ticket(ticket_create_dto, cmd.created_by_id)

        # Metadatos de ejecución (módulo/área) — post-creación
        updates = {}
        if cmd.module_origin:
            updates["module_origin"] = cmd.module_origin
        if cmd.area:
            updates["area"] = cmd.area
        if cmd.assigned_to_id:
            updates["assigned_to_id"] = cmd.assigned_to_id

        if updates:
            ticket = await self.repo.update(ticket.id, cmd.company_id, updates)

        # Forensic audit trail
        if self.audit_repo:
            await self.audit_repo.create_log(
                user_id=cmd.created_by_id,
                action="CREATE_TICKET",
                resource_id=ticket.id,
                company_id=cmd.company_id,
                details=f"Ticket created: {ticket.title}"
            )
        logger.info(f"AUDIT | User {cmd.created_by_id} | CREATE | Ticket {ticket.id} | {ticket.title}")

        return ticket

    async def handle_consume_resources(self, cmd: ConsumeResourcesCommand) -> "Ticket":  # noqa: F821
        """
        Registra recursos consumidos en el ticket y dispara movimientos de inventario.
        Sigue el patrón Atomic Outbox: si inventory falla, el commit local se aborta.
        """
        from decimal import Decimal

        ticket = await self.repo.get_by_id(cmd.ticket_id, cmd.company_id)
        if not ticket:
            raise ValueError("Ticket not found")

        for res_dto in cmd.resources:
            # 1. Llamada atómica al inventory_service — si falla, HTTPException aborta el flujo
            await self.inventory_client.record_consumption(
                company_id=cmd.company_id,
                resource_id=res_dto.resource_id,
                warehouse_id=res_dto.warehouse_id,
                quantity=Decimal(str(res_dto.quantity)),
                reference=ticket.reference_code,
                user_id=cmd.user_id
            )

        # 2. Registrar en historial
        resource_ids = [str(r.resource_id) for r in cmd.resources]
        await self.repo.add_history_entry(
            ticket_id=ticket.id,
            change_type="resources_consumed",
            old_value=None,
            new_value=f"resources: {resource_ids}",
            changed_by_id=cmd.user_id
        )

        # Forensic audit trail
        if self.audit_repo:
            await self.audit_repo.create_log(
                user_id=cmd.user_id,
                action="CONSUME_RESOURCES",
                resource_id=ticket.id,
                company_id=cmd.company_id,
                details=f"Resources consumed: {resource_ids}"
            )
        logger.info(f"AUDIT | User {cmd.user_id} | CONSUME_RESOURCES | Ticket {ticket.id} | {resource_ids}")

        return await self.repo.get_by_id(ticket.id, cmd.company_id)
