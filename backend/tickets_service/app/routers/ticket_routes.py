from typing import List, Optional
import uuid
import hmac
import hashlib
from app.core.config import settings
from common.services.audit_service import AuditService
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.services.ticket_service import TicketService
from app.schemas.ticket_dto import (
    TicketRead, 
    TicketCreate, 
    TicketUpdate, 
    TicketCommentRead, 
    TicketCommentCreate, 
    TicketCommentBase,
    ApiResponse
)
from app.schemas.internal_ticket import InternalTicketCreate
from common.security.auth_payload import TokenPayload
from app.services.ticket_commands import TicketCommandHandler, ConsumeResourcesCommand, ConsumeResourceDto

router = APIRouter(prefix="/tickets", tags=["tickets"])

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

    service = TicketService(db)
    company_id = uuid.UUID(x_company_id)
    ticket, is_new = await service.create_internal_ticket_with_debouncing(cmd, company_id)
    
    if is_new:
        return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket interno creado exitosamente")
    else:
        return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket existente (debouncing activo, duplicado prevenido)")

@router.post("/", response_model=ApiResponse)
async def create_ticket(
    cmd: TicketCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(db)
    # Seguir el multitenancy: El usuario solo puede crear tickets para su empresa o las permitidas
    # Por simplicidad usamos la del payload si no se especifica, pero el cmd pide una obligatoria
    if str(cmd.company_id) != str(user.companyId):
         raise HTTPException(status_code=403, detail="No tienes permiso para crear tickets en esta compañía")
    
    ticket = await service.create_ticket(cmd, uuid.UUID(user.sub))
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket creado exitosamente")

@router.get("/", response_model=ApiResponse)
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(db)
    tickets = await service.get_tickets(uuid.UUID(user.companyId))
    return ApiResponse(data=[TicketRead.model_validate(t) for t in tickets])

@router.get("/{ticket_id}", response_model=ApiResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user)
):
    service = TicketService(db)
    ticket = await service.get_ticket(ticket_id, uuid.UUID(user.companyId))
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
    service = TicketService(db)
    ticket = await service.update_ticket(ticket_id, uuid.UUID(user.companyId), cmd, uuid.UUID(user.sub))
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
    service = TicketService(db)
    # Validar acceso al ticket primero
    ticket = await service.get_ticket(ticket_id, uuid.UUID(user.companyId))
    if not ticket:
         raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    comment_cmd = TicketCommentCreate(
        ticket_id=ticket_id,
        company_id=uuid.UUID(user.companyId),
        content=cmd.content
    )
    comment = await service.add_comment(comment_cmd, uuid.UUID(user.sub))
    return ApiResponse(data=TicketCommentRead.model_validate(comment), message="Comentario agregado")

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
        company_id=uuid.UUID(user.companyId),
        user_id=uuid.UUID(user.sub),
        resources=resources
    )
    handler = TicketCommandHandler(db)
    
    try:
        ticket = await handler.handle_consume_resources(cmd)
    except ValueError as e:
        if str(e) == "Ticket not found":
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        raise HTTPException(status_code=400, detail=str(e))
        
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Recursos consumidos y Kardex actualizado exitosamente")

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
    service = TicketService(db)
    ticket = await service.soft_delete_ticket(ticket_id, uuid.UUID(user.companyId), uuid.UUID(user.sub))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ApiResponse(data=TicketRead.model_validate(ticket), message="Ticket eliminado (soft-delete)")

