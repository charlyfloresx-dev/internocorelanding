from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any
from decimal import Decimal
from app.core.constants import TicketStatus, TicketPriority, TicketType

class TicketBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=10)
    ticket_type: TicketType = TicketType.SUPPORT
    priority: TicketPriority = TicketPriority.MEDIUM

class TicketCreate(TicketBase):
    company_id: UUID
    # --- Fase 5: Campos operacionales opcionales ---
    module_origin: Optional[str] = None
    area: Optional[str] = None
    station_id: Optional[UUID] = None          # Requerido para MAINTENANCE
    reported_by_id: Optional[UUID] = None      # Para notificaciones de cierre
    source_service: Optional[str] = None       # "MANUAL", "INVENTORY", "MES"

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to_id: Optional[UUID] = None
    # --- Fase 5: Campos actualizables ---
    real_time_spent: Optional[int] = None      # Minutos reales invertidos
    cost_estimate: Optional[Decimal] = None    # Costo actualizado
    escalation_level: Optional[int] = None

class TicketCommentBase(BaseModel):
    content: str

class TicketCommentCreate(TicketCommentBase):
    ticket_id: UUID
    company_id: UUID

class TicketCommentRead(TicketCommentBase):
    id: UUID
    author_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TicketHistoryRead(BaseModel):
    id: UUID
    change_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class TicketResourceRead(BaseModel):
    id: UUID
    resource_id: UUID
    quantity: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

class StopLogRead(BaseModel):
    id: UUID
    station_id: UUID
    downtime_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True

class TicketRead(TicketBase):
    id: UUID
    reference_code: str
    status: TicketStatus
    assigned_to_id: Optional[UUID] = None
    module_origin: Optional[str] = None
    area: Optional[str] = None
    estimated_time: Optional[int] = None
    real_time_spent: Optional[int] = None
    cost_estimate: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    # --- Fase 5: Campos operacionales ---
    source_service: Optional[str] = None
    station_id: Optional[UUID] = None
    reported_by_id: Optional[UUID] = None
    parent_ticket_id: Optional[UUID] = None
    auto_close_on_event: Optional[str] = None
    escalation_level: int = 0
    resolved_at: Optional[datetime] = None
    # Relationships
    comments: List[TicketCommentRead] = []
    history: List[TicketHistoryRead] = []
    resources: List[TicketResourceRead] = []
    stop_logs: List[StopLogRead] = []

    class Config:
        from_attributes = True

class ApiResponse(BaseModel):
    status: str = "success"
    data: Optional[Any] = None
    message: str = ""
    meta: dict = {}
