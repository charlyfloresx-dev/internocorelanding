from typing import List, Optional
import uuid
import hmac
import hashlib
import csv
import io
from datetime import datetime, timezone
from tickets_app.core.config import settings
from common.services.audit_service import AuditService
from fastapi import APIRouter, Depends, HTTPException, Query, Header, WebSocket, WebSocketDisconnect, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from tickets_app.dependencies.database import get_db
from common.security.dependencies import require_scope
from tickets_app.services.ticket_service import TicketService
from tickets_app.schemas.ticket_dto import (
    TicketRead,
    TicketCreate,
    TicketUpdate,
    TicketCommentRead,
    TicketCommentCreate,
    TicketCommentBase,
    TicketTriage,
    TicketActionCreate,
    TicketActionClose,
    TicketActionRead,
    TicketAssignRequest,
    TicketEscalateRequest,
    TicketBulkCreateRow,
    TicketBulkCreateResult,
    TicketBulkImportResponse,
    ApiResponse
)
from tickets_app.core.constants import TicketStatus, TicketPriority
from tickets_app.schemas.escalation_dto import EscalationRuleRead
from tickets_app.schemas.internal_ticket import InternalTicketCreate, InternalTicketResolve
from common.infrastructure.websocket import manager
from common.security.auth_payload import TokenPayload
from tickets_app.services.ticket_commands import TicketCommandHandler, ConsumeResourcesCommand, ConsumeResourceDto
from tickets_app.infrastructure.repositories.ticket_repository import SQLAlchemyTicketRepository
from tickets_app.infrastructure.repositories.escalation_repository import SQLAlchemyEscalationRepository
from tickets_app.infrastructure.inventory_client import HttpInventoryClient
from tickets_app.services.escalation_service import EscalationConfigService
from tickets_app.infrastructure.station_websocket_manager import station_manager

def to_uuid(val) -> Optional[uuid.UUID]:
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    return uuid.UUID(str(val))

router = APIRouter(tags=["tickets"])

@router.get("/technicians/workload")
@router.get("/technicians/workload/")
async def get_technicians_workload(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    """
    Retorna la carga de trabajo actual de los técnicos del tenant.
    Útil para el triaje inteligente en el Dashboard.
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    workload = await service.get_technician_workload(to_uuid(user.company_id))
    return ApiResponse(data=workload, message="Carga de trabajo obtenida")


@router.post("/internal", response_model=ApiResponse)
async def create_internal_ticket(
    cmd: InternalTicketCreate,
    db: AsyncSession = Depends(get_db),
    x_company_id: str = Header(..., alias="X-Company-ID"),
    x_service_signature: str = Header(None, alias="X-Service-Signature"),
):
    """
    Endpoint inter-servicio para creación automática de tickets.
    Invocado por inventory_service u otros servicios internos.
    Incluye lógica de debouncing SHA256 para prevenir duplicados.
    """
    if not x_service_signature:
        await AuditService.track(
            user_id="SYSTEM",
            action="UNAUTHORIZED_ACCESS",
            resource="ticket_internal_api",
            metadata={"company_id": str(x_company_id), "details": "Missing HMAC signature"}
        )
        raise HTTPException(status_code=403, detail="Firma de servicio requerida")

    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        x_company_id.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_service_signature):
        await AuditService.track(
            user_id="SYSTEM",
            action="UNAUTHORIZED_ACCESS",
            resource="ticket_internal_api",
            metadata={"company_id": str(x_company_id), "details": "Invalid HMAC signature"}
        )
        raise HTTPException(status_code=403, detail="Firma de servicio inválida")

    service = TicketService(SQLAlchemyTicketRepository(db))
    company_id = uuid.UUID(x_company_id)
    ticket, is_new = await service.create_internal_ticket_with_debouncing(cmd, company_id)
    
    if is_new:
        return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket interno creado exitosamente")
    else:
        return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket existente (debouncing activo, duplicado prevenido)")

@router.post("/internal/resolve", response_model=ApiResponse)
async def resolve_internal_ticket(
    cmd: InternalTicketResolve,
    db: AsyncSession = Depends(get_db),
    x_company_id: str = Header(..., alias="X-Company-ID"),
    x_service_signature: str = Header(None, alias="X-Service-Signature"),
):
    """
    Endpoint inter-servicio para auto-cierre de tickets.
    Disparado cuando un evento operacional resuelve el origen del ticket 
    (ej. KARDEX_ENTRY_CONFIRMED para MATERIAL_RECEIPT).
    """
    if not x_service_signature:
        await AuditService.track(
            user_id="SYSTEM",
            action="UNAUTHORIZED_ACCESS",
            resource="ticket_internal_api",
            metadata={"company_id": str(x_company_id), "details": "Missing HMAC signature for resolve"}
        )
        raise HTTPException(status_code=403, detail="Firma de servicio requerida")

    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        x_company_id.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(x_service_signature, expected_signature):
        await AuditService.track(
            user_id="SYSTEM",
            action="UNAUTHORIZED_ACCESS",
            resource="ticket_internal_api",
            metadata={"company_id": str(x_company_id), "details": "Invalid HMAC signature for resolve"}
        )
        raise HTTPException(status_code=403, detail="Firma de servicio inválida")

    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.resolve_internal_ticket_by_event(cmd, uuid.UUID(x_company_id))
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado o ya resuelto")
        
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket auto-resuelto exitosamente")

@router.post("/internal/resolve-by-station", response_model=ApiResponse)
async def resolve_tickets_by_station_endpoint(
    station_id: uuid.UUID,
    trigger_event: str,
    db: AsyncSession = Depends(get_db),
    x_company_id: str = Header(..., alias="X-Company-ID"),
    x_service_signature: str = Header(None, alias="X-Service-Signature"),
):
    """
    Endpoint inter-servicio para auto-cierre masivo por estación.
    Invocado por mes_service cuando se confirma una intervención en Workstation.
    """
    if not x_service_signature:
        raise HTTPException(status_code=403, detail="Firma de servicio requerida")

    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        x_company_id.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(x_service_signature, expected_signature):
        raise HTTPException(status_code=403, detail="Firma de servicio inválida")

    service = TicketService(SQLAlchemyTicketRepository(db))
    tickets = await service.resolve_tickets_by_station(
        station_id=station_id,
        company_id=uuid.UUID(x_company_id),
        trigger_event=trigger_event,
        source_service="MES",
        notes="Resolución automática tras cierre de downtime en MES Workstation"
    )
    
    return ApiResponse(
        data={"resolved_count": len(tickets)}, 
        message=f"{len(tickets)} tickets auto-resueltos para la estación {station_id}"
    )

@router.post("/", response_model=ApiResponse)
async def create_ticket(
    cmd: TicketCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:write"]))
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    # Seguir el multitenancy: El usuario solo puede crear tickets para su empresa o las permitidas
    # Por simplicidad usamos la del payload si no se especifica, pero el cmd pide una obligatoria
    if str(cmd.company_id) != str(user.company_id):
         raise HTTPException(status_code=403, detail="No tienes permiso para crear tickets en esta compañía")
    
    ticket = await service.create_ticket(cmd, to_uuid(user.sub))

    # Broadcast en tiempo real
    await manager.broadcast_to_company(
        str(user.company_id),
        {
            "type": "TICKET_CREATED",
            "payload": TicketRead.model_validate(ticket).model_dump()
        }
    )

    # Emit WebSocket event for station realtime listeners
    if ticket.station_id:
        await station_manager.emit_ticket_event(
            event_type="ticket.created",
            ticket_id=str(ticket.id),
            station_id=str(ticket.station_id),
            priority=ticket.priority,
            status=ticket.status
        )

    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket creado exitosamente")

@router.get("/", response_model=ApiResponse)
async def list_tickets(
    station_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    """
    Lista tickets de la empresa. Filtros opcionales:
    - station_id: filtra por recurso/estación MES (para el tab Soporte del monitor)
    - status: filtra por estado (NEW, ASSIGNED, IN_PROGRESS, etc.)
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    tickets = await service.get_tickets(
        to_uuid(user.company_id),
        station_id=station_id,
        status=status,
    )
    return ApiResponse(data=[TicketRead.model_validate(t) for t in tickets])

@router.get("/mine", response_model=ApiResponse)
async def list_my_tickets(
    department_id: Optional[uuid.UUID] = None,
    collaborator_id: Optional[uuid.UUID] = None,
    external_contact_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    """
    Retorna tickets asignados al usuario actual en cualquiera de sus identidades:
    INTERNAL (user_id), PLANTA (collaborator_id), EXTERNO (external_contact_id).
    """
    service = TicketService(SQLAlchemyTicketRepository(db))

    dept_id = department_id
    if not dept_id and hasattr(user, "department_id") and user.department_id:
        try:
            dept_id = to_uuid(user.department_id)
        except Exception:
            pass

    tickets = await service.get_tickets_with_visibility(
        company_id=to_uuid(user.company_id),
        user_id=to_uuid(user.sub),
        is_admin=False,
        is_supervisor=False,
        department_id=dept_id,
        collaborator_id=collaborator_id,
        external_contact_id=external_contact_id,
    )
    return ApiResponse(data=[TicketRead.model_validate(t) for t in tickets])

@router.post("/{ticket_id}/triage", response_model=ApiResponse)
async def triage_ticket(
    ticket_id: uuid.UUID,
    cmd: TicketTriage,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:triage"]))
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    is_supervisor = "supervisor" in [r.lower() for r in user.role_names] or "admin" in [r.lower() for r in user.role_names]
    try:
        ticket = await service.triage_ticket(
            ticket_id=ticket_id,
            company_id=to_uuid(user.company_id),
            cmd=cmd,
            user_id=to_uuid(user.sub),
            is_supervisor=is_supervisor
        )
        
        # Broadcast en tiempo real
        await manager.broadcast_to_company(
            str(user.company_id),
            {
                "type": "TICKET_UPDATE",
                "payload": TicketRead.model_validate(ticket).model_dump()
            }
        )
        
        return ApiResponse(data=TicketRead.model_validate(ticket), message="Triaje completado exitosamente")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{ticket_id}", response_model=ApiResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.get_ticket(ticket_id, to_uuid(user.company_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ApiResponse(data=TicketRead.model_validate(ticket))

@router.patch("/{ticket_id}", response_model=ApiResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    cmd: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:write"]))
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.update_ticket(ticket_id, to_uuid(user.company_id), cmd, to_uuid(user.sub))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # Broadcast en tiempo real
    await manager.broadcast_to_company(
        str(user.company_id),
        {
            "type": "TICKET_UPDATE",
            "payload": TicketRead.model_validate(ticket).model_dump()
        }
    )

    # Emit WebSocket event for station realtime listeners
    if ticket.station_id:
        event_type = "ticket.status_changed" if cmd.status else "ticket.updated"
        await station_manager.emit_ticket_event(
            event_type=event_type,
            ticket_id=str(ticket.id),
            station_id=str(ticket.station_id),
            priority=ticket.priority,
            status=ticket.status
        )

    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket actualizado")

@router.post("/{ticket_id}/comments", response_model=ApiResponse)
async def add_comment(
    ticket_id: uuid.UUID,
    cmd: TicketCommentBase, # Solo contenido
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:write"]))
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    # Validar acceso al ticket primero
    ticket = await service.get_ticket(ticket_id, to_uuid(user.company_id))
    if not ticket:
         raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    comment_cmd = TicketCommentCreate(
        ticket_id=ticket_id,
        company_id=to_uuid(user.company_id),
        content=cmd.content
    )
    comment = await service.add_comment(comment_cmd, to_uuid(user.sub))
    return ApiResponse(data=TicketCommentRead.model_validate(comment), message="Comentario agregado")

@router.get("/{ticket_id}/comments", response_model=ApiResponse)
async def list_comments(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.get_ticket(ticket_id, to_uuid(user.company_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # Los comentarios ya vienen en el ticket por el selectinload del repo
    return ApiResponse(data=[TicketCommentRead.model_validate(c) for c in ticket.comments])

@router.post("/{ticket_id}/assign", response_model=ApiResponse)
async def assign_ticket(
    ticket_id: uuid.UUID,
    cmd: TicketAssignRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:write"]))
):
    """
    Asigna un ticket a un colaborador, usuario externo, o departamento.
    Transición automática a estado ASSIGNED si es NEW.
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    company_id = to_uuid(user.company_id)

    # Validar que el ticket existe
    ticket = await service.get_ticket(ticket_id, company_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # Construir TicketUpdate con los datos de asignación
    update_cmd = TicketUpdate(
        assigned_to_id=cmd.assigned_to_id,
        collaborator_id=cmd.collaborator_id,
        external_contact_id=cmd.external_contact_id,
        assigned_department_id=cmd.assigned_department_id,
        is_external=cmd.is_external,
        # Transición automática a ASSIGNED si es NEW
        status=TicketStatus.ASSIGNED if ticket.status == TicketStatus.NEW else None
    )

    updated_ticket = await service.update_ticket(ticket_id, company_id, update_cmd, to_uuid(user.sub))

    # Broadcast en tiempo real
    await manager.broadcast_to_company(
        str(company_id),
        {
            "type": "TICKET_ASSIGNED",
            "payload": TicketRead.model_validate(updated_ticket).model_dump()
        }
    )

    # Emit WebSocket event for station realtime listeners
    if updated_ticket.station_id:
        await station_manager.emit_ticket_event(
            event_type="ticket.assigned",
            ticket_id=str(updated_ticket.id),
            station_id=str(updated_ticket.station_id),
            priority=updated_ticket.priority,
            status=updated_ticket.status
        )

    return ApiResponse(data=TicketRead.model_validate(updated_ticket), message="Ticket asignado exitosamente")

@router.post("/{ticket_id}/escalate", response_model=ApiResponse)
async def escalate_ticket(
    ticket_id: uuid.UUID,
    cmd: TicketEscalateRequest,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:write"]))
):
    """
    Escala un ticket a prioridad CRITICAL y notifica al supervisor.
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    company_id = to_uuid(user.company_id)

    # Validar que el ticket existe
    ticket = await service.get_ticket(ticket_id, company_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # No escalar si ya es CRITICAL
    if ticket.priority == TicketPriority.CRITICAL:
        return ApiResponse(
            data=TicketRead.model_validate(ticket),
            message="El ticket ya está escalado a CRITICAL"
        )

    # Construir TicketUpdate con escalación
    update_cmd = TicketUpdate(
        priority=cmd.priority
    )

    updated_ticket = await service.update_ticket(ticket_id, company_id, update_cmd, to_uuid(user.sub))

    # Broadcast en tiempo real
    await manager.broadcast_to_company(
        str(company_id),
        {
            "type": "TICKET_ESCALATED",
            "payload": TicketRead.model_validate(updated_ticket).model_dump()
        }
    )

    return ApiResponse(data=TicketRead.model_validate(updated_ticket), message="Ticket escalado a CRITICAL")

@router.post("/{ticket_id}/consume-resources", response_model=ApiResponse)
async def consume_ticket_resources(
    ticket_id: uuid.UUID,
    resources: List[ConsumeResourceDto],
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:write"]))
):
    """
    CQRS: Registra consumo de recursos operacionales.
    Dispara integración atómica POST /transactions/ hacia inventory_service (Kardex OUT).
    """
    cmd = ConsumeResourcesCommand(
        ticket_id=ticket_id,
        company_id=to_uuid(user.company_id),
        user_id=to_uuid(user.sub),
        resources=resources
    )
    handler = TicketCommandHandler(SQLAlchemyTicketRepository(db), HttpInventoryClient())
    
    try:
        ticket = await handler.handle_consume_resources(cmd)
    except ValueError as e:
        if str(e) == "Ticket not found":
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        raise HTTPException(status_code=400, detail=str(e))
        
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Recursos consumidos y Kardex actualizado exitosamente")

@router.post("/admin/seed-escalation-rules", response_model=ApiResponse)
async def seed_escalation_rules(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["admin"]))
):
    """
    Bootstrap: Pueba las reglas de escalación dinámicas para la empresa actual.
    Solo para administradores o desarrollo inicial.
    """
    repo = SQLAlchemyEscalationRepository(db)
    service = EscalationConfigService(repo)
    
    await service.seed_default_rules(to_uuid(user.company_id))
    await db.commit()
    
    return ApiResponse(data=None, message="Matriz de escalación dinamizada y sembrada exitosamente")

@router.get("/config/escalation-rules", response_model=ApiResponse)
async def get_escalation_rules(
    area: str = Query(..., description="Área operacional (Producción, Almacén, etc.)"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    """
    Retorna la configuración activa de escalación para un área.
    Falla hacia '_default' si el área no existe.
    """
    repo = SQLAlchemyEscalationRepository(db)
    service = EscalationConfigService(repo)
    
    rules = await service.get_escalation_path(to_uuid(user.company_id), area)
    return ApiResponse(
        data=[EscalationRuleRead.model_validate(r) for r in rules], 
        message=f"Reglas de escalación para {area} obtenidas"
    )

@router.get("/config/constants", response_model=ApiResponse)
async def get_ticket_constants():
    """
    Expone los Enums del backend para sincronización con el frontend.
    """
    from tickets_app.core.constants import TicketStatus, TicketPriority, TicketType
    return ApiResponse(
        data={
            "statuses": [s.value for s in TicketStatus],
            "priorities": [p.value for p in TicketPriority],
            "types": [t.value for t in TicketType]
        },
        message="Constantes de tickets obtenidas exitosamente"
    )

@router.delete("/{ticket_id}", response_model=ApiResponse)
async def delete_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:delete"]))
):
    """
    Soft-delete: marca is_active=False para mantener integridad referencial
    y cumplir con las políticas de auditoría forense.
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.soft_delete_ticket(ticket_id, to_uuid(user.company_id), to_uuid(user.sub))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket eliminado (soft-delete)")


@router.get("/public/access", response_model=ApiResponse)
async def get_public_ticket_access(
    token: str = Query(..., description="Industrial External Token"),
    db: AsyncSession = Depends(get_db)
):
    """
    [Phase 89] Public access for external providers via token.
    Does NOT require authentication header.
    """
    repo = SQLAlchemyTicketRepository(db)
    
    # Simple token validation (it's stored in the 'external_token' column)
    ticket = await repo.get_by_external_token(token)
    if not ticket:
        raise HTTPException(status_code=404, detail="Industrial access denied: Invalid or expired token")
        
    return ApiResponse(
        status="success",
        data=TicketRead.model_validate(ticket),
        message="Industrial access granted"
    )

@router.post("/public/comments", response_model=ApiResponse)
async def add_public_comment(
    cmd: TicketCommentBase,
    token: str = Query(..., description="Industrial External Token"),
    db: AsyncSession = Depends(get_db)
):
    """
    [Phase 89] Allow external providers to add comments using their token.
    """
    repo = SQLAlchemyTicketRepository(db)
    ticket = await repo.get_by_external_token(token)
    if not ticket:
        raise HTTPException(status_code=404, detail="Industrial access denied")
        
    service = TicketService(repo)
    # Usamos el ID de sistema para acciones de proveedores externos por ahora
    # En una fase futura, podríamos vincularlo al ExternalContact.id
    system_user_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
    
    comment_cmd = TicketCommentCreate(
        ticket_id=ticket.id,
        company_id=ticket.company_id,
        content=cmd.content
    )
    comment = await service.add_comment(comment_cmd, system_user_id)
    
    # Broadcast en tiempo real para que el dashboard interno vea el comentario
    await manager.broadcast_to_company(
        str(ticket.company_id),
        {
            "type": "TICKET_COMMENT_ADDED",
            "payload": TicketCommentRead.model_validate(comment).model_dump()
        }
    )
    
    return ApiResponse(data=TicketCommentRead.model_validate(comment), message="Comentario agregado por proveedor externo")


# ─────────────────────────────────────────────────────────────
#  TICKET ACTIONS
# ─────────────────────────────────────────────────────────────

@router.post("/{ticket_id}/actions", response_model=ApiResponse)
async def create_ticket_action(
    ticket_id: uuid.UUID,
    cmd: TicketActionCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:triage"]))
):
    from tickets_app.models.action import TicketAction

    company_id = to_uuid(user.company_id)
    action = TicketAction(
        id=uuid.uuid4(),
        ticket_id=ticket_id,
        company_id=company_id,
        tenant_id=company_id,
        description=cmd.description,
        created_by=to_uuid(user.sub),
        assigned_to_id=cmd.assigned_to_id,
        collaborator_id=cmd.collaborator_id,
        external_contact_id=cmd.external_contact_id,
        commit_date=cmd.commit_date,
        escalation_date=cmd.escalation_date,
        is_closed=False,
        version_id=1,
        is_active=True,
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)
    return ApiResponse(data=TicketActionRead.model_validate(action), message="Acción creada")


@router.get("/{ticket_id}/actions", response_model=ApiResponse)
async def list_ticket_actions(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    from tickets_app.models.action import TicketAction
    from sqlalchemy import select

    company_id = to_uuid(user.company_id)
    result = await db.execute(
        select(TicketAction).where(
            TicketAction.ticket_id == ticket_id,
            TicketAction.company_id == company_id,
            TicketAction.is_active == True
        ).order_by(TicketAction.created_at)
    )
    actions = result.scalars().all()
    return ApiResponse(data=[TicketActionRead.model_validate(a) for a in actions])


@router.patch("/{ticket_id}/actions/{action_id}/close", response_model=ApiResponse)
async def close_ticket_action(
    ticket_id: uuid.UUID,
    action_id: uuid.UUID,
    cmd: TicketActionClose,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:triage"]))
):
    from tickets_app.models.action import TicketAction
    from sqlalchemy import select
    from datetime import datetime, timezone

    company_id = to_uuid(user.company_id)
    result = await db.execute(
        select(TicketAction).where(
            TicketAction.id == action_id,
            TicketAction.ticket_id == ticket_id,
            TicketAction.company_id == company_id,
        )
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Acción no encontrada")

    action.is_closed = True
    action.closed_date = cmd.closed_date or datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(action)
    return ApiResponse(data=TicketActionRead.model_validate(action), message="Acción cerrada")


@router.post("/bulk-import", response_model=ApiResponse)
async def bulk_import_tickets(
    file: UploadFile = File(..., description="CSV file with tickets"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:write"]))
):
    """
    Bulk import tickets from CSV file.
    CSV columns: title, description, ticket_type, priority, area, module_origin
    Returns summary of created tickets and errors.
    """
    company_id = to_uuid(user.company_id)
    user_id = to_uuid(user.sub)

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file (.csv)")

    # Validate file size (max 5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")

    # Parse CSV
    try:
        csv_text = contents.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(csv_reader)

        if not rows:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        # Validate headers
        required_columns = {"title", "description"}
        if not required_columns.issubset(set(csv_reader.fieldnames or [])):
            raise HTTPException(
                status_code=400,
                detail=f"CSV must contain columns: {', '.join(required_columns)}"
            )
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid UTF-8 encoding in CSV file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    # Process rows
    service = TicketService(SQLAlchemyTicketRepository(db))
    results: List[TicketBulkCreateResult] = []
    successful_count = 0

    for row_num, row in enumerate(rows, start=1):
        try:
            # Validate and parse row
            ticket_row = TicketBulkCreateRow(
                title=row.get("title", "").strip(),
                description=row.get("description", "").strip(),
                ticket_type=row.get("ticket_type", "SUPPORT").strip(),
                priority=row.get("priority", "MEDIA").strip(),
                area=row.get("area", "").strip() or None,
                module_origin=row.get("module_origin", "").strip() or None,
            )

            # Validate ticket_type enum
            try:
                from tickets_app.core.constants import TicketType
                ticket_type_enum = TicketType(ticket_row.ticket_type)
            except ValueError:
                raise ValueError(f"Invalid ticket_type: {ticket_row.ticket_type}")

            # Validate priority enum
            try:
                priority_enum = TicketPriority(ticket_row.priority)
            except ValueError:
                raise ValueError(f"Invalid priority: {ticket_row.priority}")

            # Create ticket
            create_cmd = TicketCreate(
                title=ticket_row.title,
                description=ticket_row.description,
                ticket_type=ticket_type_enum,
                priority=priority_enum,
                company_id=company_id,
                area=ticket_row.area,
                module_origin=ticket_row.module_origin,
                source_service="BULK_IMPORT"
            )

            ticket = await service.create_ticket(create_cmd, user_id)

            results.append(TicketBulkCreateResult(
                row_number=row_num,
                success=True,
                ticket_id=ticket.id,
                reference_code=ticket.reference_code,
                error=None
            ))
            successful_count += 1

            # Broadcast created event (station-scoped if station_id present)
            if ticket.station_id:
                await station_manager.emit_ticket_event(
                    event_type="ticket.created",
                    ticket_id=str(ticket.id),
                    station_id=str(ticket.station_id),
                    priority=ticket.priority,
                    status=ticket.status
                )

        except Exception as e:
            results.append(TicketBulkCreateResult(
                row_number=row_num,
                success=False,
                ticket_id=None,
                reference_code=None,
                error=str(e)
            ))

    response = TicketBulkImportResponse(
        total_rows=len(rows),
        successful=successful_count,
        failed=len(rows) - successful_count,
        results=results,
        created_at=datetime.now(timezone.utc)
    )

    await db.commit()

    return ApiResponse(
        data=response.model_dump(),
        message=f"Bulk import completed: {successful_count}/{len(rows)} tickets created"
    )


# ── WebSocket Realtime Ticket Updates ─────────────────────────────────────

@router.websocket("/realtime/{station_id}")
async def websocket_realtime_tickets(websocket: WebSocket, station_id: str):
    """
    WebSocket endpoint for real-time ticket updates per MES resource (station).

    Clients connect to /tickets/realtime/{station_id} and receive events:
    - ticket.created: New ticket assigned to this station
    - ticket.updated: Status, priority, or other field updated
    - ticket.assigned: Ticket assigned to someone
    - ticket.status_changed: Status transitions (DRAFT → IN_PROGRESS → etc.)

    Event payload structure:
    {
        "event_type": "ticket.created|updated|assigned|status_changed",
        "ticket_id": "uuid",
        "station_id": "uuid",
        "priority": "CRÍTICA|ALTA|MEDIA|BAJA",
        "status": "Nuevo|Pendiente...",
        "timestamp": "2026-06-03T02:59:00Z"
    }

    The server sends events to all connected clients for the same station_id.
    Clients implement exponential backoff reconnection if connection drops.
    """
    await station_manager.connect(websocket, station_id)
    try:
        # Keep connection alive and accept any incoming messages
        # (in case we want to add client->server messages in the future)
        while True:
            data = await websocket.receive_text()
            # For now, we don't process client messages
            # Just keep the connection open for server→client broadcasts
    except WebSocketDisconnect:
        station_manager.disconnect(websocket, station_id)

