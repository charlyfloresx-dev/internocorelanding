from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import uuid
from decimal import Decimal
from common.services.audit_service import AuditService

from tickets_app.domain.ports.ticket_repository import ITicketRepository
from tickets_app.domain.ports.inventory_client import IInventoryClient
from tickets_app.services.ticket_service import TicketService
from tickets_app.schemas.ticket_dto import TicketCreate
from tickets_app.models.ticket import Ticket
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
    # --- Fase 5: Campos Operacionales ---
    station_id: Optional[UUID] = None
    reported_by_id: Optional[UUID] = None
    parent_ticket_id: Optional[UUID] = None
    source_service: Optional[str] = None
    escalation_level: int = 0
    collaborator_id: Optional[UUID] = None
    external_contact_id: Optional[UUID] = None
    is_external: bool = False


class ConsumeResourceDto(BaseModel):
    resource_id: UUID
    warehouse_id: UUID
    quantity: Decimal


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
            company_id=cmd.company_id,
            assigned_to_id=cmd.assigned_to_id,
            collaborator_id=cmd.collaborator_id,
            external_contact_id=cmd.external_contact_id,
            is_external=cmd.is_external,
            module_origin=cmd.module_origin,
            area=cmd.area,
            station_id=cmd.station_id,
            reported_by_id=cmd.reported_by_id,
            source_service=cmd.source_service
        )

        ticket = await self._service.create_ticket(ticket_create_dto, cmd.created_by_id)

        # Metadatos de ejecución (módulo/área/operacionales) — post-creación
        updates = {}
        if cmd.module_origin:
            updates["module_origin"] = cmd.module_origin
        if cmd.area:
            updates["area"] = cmd.area
        if cmd.assigned_to_id:
            updates["assigned_to_id"] = cmd.assigned_to_id
        if cmd.station_id:
            updates["station_id"] = cmd.station_id
        if cmd.reported_by_id:
            updates["reported_by_id"] = cmd.reported_by_id
        if cmd.parent_ticket_id:
            updates["parent_ticket_id"] = cmd.parent_ticket_id
        if cmd.source_service:
            updates["source_service"] = cmd.source_service
        if cmd.escalation_level > 0:
            updates["escalation_level"] = cmd.escalation_level

        if updates:
            ticket = await self.repo.update(ticket.id, cmd.company_id, updates)

        # Forensic audit trail
        action_name = "EXTERNAL_PROVIDER_ACTION" if cmd.is_external else "CREATE_TICKET"
        await AuditService.track(
            user_id=cmd.created_by_id,
            action=action_name,
            resource=f"ticket:{ticket.id}",
            metadata={
                "company_id": str(cmd.company_id),
                "details": f"Ticket created: {ticket.title}",
                "collaborator_id": str(cmd.collaborator_id) if cmd.collaborator_id else None,
                "external_contact_id": str(cmd.external_contact_id) if cmd.external_contact_id else None
            }
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
            company_id=cmd.company_id,
            change_type="resources_consumed",
            old_value=None,
            new_value=f"resources: {resource_ids}",
            changed_by_id=cmd.user_id
        )

        # Forensic audit trail
        await AuditService.track(
            user_id=cmd.user_id,
            action="CONSUME_RESOURCES",
            resource=f"ticket:{ticket.id}",
            metadata={
                "company_id": str(cmd.company_id),
                "details": f"Resources consumed: {resource_ids}"
            }
        )
        logger.info(f"AUDIT | User {cmd.user_id} | CONSUME_RESOURCES | Ticket {ticket.id} | {resource_ids}")

        return await self.repo.get_by_id(ticket.id, cmd.company_id)
