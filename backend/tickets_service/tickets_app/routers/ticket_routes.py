from typing import List, Optional
import uuid
import hmac
import hashlib
from tickets_app.core.config import settings
from common.services.audit_service import AuditService
from fastapi import APIRouter, Depends, HTTPException, Query, Header
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
    ApiResponse
)
from tickets_app.schemas.escalation_dto import EscalationRuleRead
from tickets_app.schemas.internal_ticket import InternalTicketCreate, InternalTicketResolve
from common.infrastructure.websocket import manager
from common.security.auth_payload import TokenPayload
from tickets_app.services.ticket_commands import TicketCommandHandler, ConsumeResourcesCommand, ConsumeResourceDto
from tickets_app.infrastructure.repositories.ticket_repository import SQLAlchemyTicketRepository
from tickets_app.infrastructure.repositories.escalation_repository import SQLAlchemyEscalationRepository
from tickets_app.infrastructure.inventory_client import HttpInventoryClient
from tickets_app.services.escalation_service import EscalationConfigService

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
    
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket creado exitosamente")

@router.get("/", response_model=ApiResponse)
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    service = TicketService(SQLAlchemyTicketRepository(db))
    tickets = await service.get_tickets(to_uuid(user.company_id))
    return ApiResponse(data=[TicketRead.model_validate(t) for t in tickets])

@router.get("/mine", response_model=ApiResponse)
async def list_my_tickets(
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_scope(["ticket:read"]))
):
    """
    Retorna tickets creados por o asignados al usuario actual en su empresa activa.
    Soporta filtrado por departamento/área del operador de forma polimórfica.
    """
    service = TicketService(SQLAlchemyTicketRepository(db))
    
    dept_id = department_id
    if not dept_id and hasattr(user, "department_id") and user.department_id:
        try:
            dept_id = to_uuid(user.department_id)
        except Exception:
            pass

    # Usamos list_by_visibility con flags de usuario normal para filtrar lo propio
    tickets = await service.get_tickets_with_visibility(
        company_id=to_uuid(user.company_id),
        user_id=to_uuid(user.sub),
        is_admin=False,
        is_supervisor=False,
        department_id=dept_id
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

