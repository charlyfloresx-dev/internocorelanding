from typing import List, Optional
import uuid
import hmac
import hashlib
from tickets_app.core.config import settings
from common.services.audit_service import AuditService
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from tickets_app.dependencies.database import get_db
from tickets_app.dependencies.auth import get_current_user
from tickets_app.services.ticket_service import TicketService
from tickets_app.schemas.ticket_dto import (
    TicketRead, 
    TicketCreate, 
    TicketUpdate, 
    TicketCommentRead, 
    TicketCommentCreate, 
    TicketCommentBase,
    TicketTriage,
    ApiResponse
)
from tickets_app.schemas.escalation_dto import EscalationRuleRead
from tickets_app.schemas.internal_ticket import InternalTicketCreate, InternalTicketResolve
from common.security.auth_payload import TokenPayload
from tickets_app.services.ticket_commands import TicketCommandHandler, ConsumeResourcesCommand, ConsumeResourceDto
from tickets_app.infrastructure.repositories.ticket_repository import SQLAlchemyTicketRepository
from tickets_app.infrastructure.repositories.escalation_repository import SQLAlchemyEscalationRepository
from tickets_app.infrastructure.inventory_client import HttpInventoryClient
from tickets_app.services.escalation_service import EscalationConfigService

router = APIRouter(tags=["tickets"])

@router.get("/technicians/workload")
@router.get("/technicians/workload/")
async def get_technicians_workload(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    """
    Retorna la carga de trabajo actual de los técnicos del tenant.
    Útil para el triaje inteligente en el Dashboard.
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    workload = await service.get_technician_workload(uuid.UUID(user.company_id))
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
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    # Seguir el multitenancy: El usuario solo puede crear tickets para su empresa o las permitidas
    # Por simplicidad usamos la del payload si no se especifica, pero el cmd pide una obligatoria
    if str(cmd.company_id) != str(user.company_id):
         raise HTTPException(status_code=403, detail="No tienes permiso para crear tickets en esta compañía")
    
    ticket = await service.create_ticket(cmd, uuid.UUID(user.sub))
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket creado exitosamente")

@router.get("/", response_model=ApiResponse)
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    tickets = await service.get_tickets(uuid.UUID(user.company_id))
    return ApiResponse(data=[TicketRead.model_validate(t) for t in tickets])

@router.post("/{ticket_id}/triage", response_model=ApiResponse)
async def triage_ticket(
    ticket_id: uuid.UUID,
    cmd: TicketTriage,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    is_supervisor = "supervisor" in [r.lower() for r in user.role_names] or "admin" in [r.lower() for r in user.role_names]
    try:
        ticket = await service.triage_ticket(
            ticket_id=ticket_id,
            company_id=uuid.UUID(user.company_id),
            cmd=cmd,
            user_id=uuid.UUID(user.sub),
            is_supervisor=is_supervisor
        )
        return ApiResponse(data=TicketRead.model_validate(ticket), message="Triaje completado exitosamente")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))



@router.get("/{ticket_id}", response_model=ApiResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.get_ticket(ticket_id, uuid.UUID(user.company_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ApiResponse(data=TicketRead.model_validate(ticket))

@router.patch("/{ticket_id}", response_model=ApiResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    cmd: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.update_ticket(ticket_id, uuid.UUID(user.company_id), cmd, uuid.UUID(user.sub))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket actualizado")

@router.post("/{ticket_id}/comments", response_model=ApiResponse)
async def add_comment(
    ticket_id: uuid.UUID,
    cmd: TicketCommentBase, # Solo contenido
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    # Validar acceso al ticket primero
    ticket = await service.get_ticket(ticket_id, uuid.UUID(user.company_id))
    if not ticket:
         raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    comment_cmd = TicketCommentCreate(
        ticket_id=ticket_id,
        company_id=uuid.UUID(user.company_id),
        content=cmd.content
    )
    comment = await service.add_comment(comment_cmd, uuid.UUID(user.sub))
    return ApiResponse(data=TicketCommentRead.model_validate(comment), message="Comentario agregado")

@router.get("/{ticket_id}/comments", response_model=ApiResponse)
async def list_comments(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.get_ticket(ticket_id, uuid.UUID(user.company_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    # Los comentarios ya vienen en el ticket por el selectinload del repo
    return ApiResponse(data=[TicketCommentRead.model_validate(c) for c in ticket.comments])

@router.post("/{ticket_id}/consume-resources", response_model=ApiResponse)
async def consume_ticket_resources(
    ticket_id: uuid.UUID,
    resources: List[ConsumeResourceDto],
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    """
    CQRS: Registra consumo de recursos operacionales.
    Dispara integración atómica POST /transactions/ hacia inventory_service (Kardex OUT).
    """
    cmd = ConsumeResourcesCommand(
        ticket_id=ticket_id,
        company_id=uuid.UUID(user.company_id),
        user_id=uuid.UUID(user.sub),
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
    user: TokenPayload = Depends(get_current_user)
):
    """
    Bootstrap: Pueba las reglas de escalación dinámicas para la empresa actual.
    Solo para administradores o desarrollo inicial.
    """
    repo = SQLAlchemyEscalationRepository(db)
    service = EscalationConfigService(repo)
    
    await service.seed_default_rules(uuid.UUID(user.company_id))
    await db.commit()
    
    return ApiResponse(data=None, message="Matriz de escalación dinamizada y sembrada exitosamente")

@router.get("/config/escalation-rules", response_model=ApiResponse)
async def get_escalation_rules(
    area: str = Query(..., description="Área operacional (Producción, Almacén, etc.)"),
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    """
    Retorna la configuración activa de escalación para un área.
    Falla hacia '_default' si el área no existe.
    """
    repo = SQLAlchemyEscalationRepository(db)
    service = EscalationConfigService(repo)
    
    rules = await service.get_escalation_path(uuid.UUID(user.company_id), area)
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
    user: TokenPayload = Depends(get_current_user)
):
    """
    Soft-delete: marca is_active=False para mantener integridad referencial
    y cumplir con las políticas de auditoría forense.
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    ticket = await service.soft_delete_ticket(ticket_id, uuid.UUID(user.company_id), uuid.UUID(user.sub))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket eliminado (soft-delete)")

