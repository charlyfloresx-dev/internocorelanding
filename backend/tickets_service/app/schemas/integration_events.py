from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
import uuid
from datetime import datetime
from app.core.constants import TicketPriority, TicketType

class TicketCreatedEvent(BaseModel):
    """
    JSON Contract for the `TicketCreatedEvent`.
    Dispatched by tickets_service to be consumed by notification_service
    or any other interested subscriber.
    """
    event_id: UUID = Field(default_factory=uuid.uuid4, description="Idempotency Key for consumers")
    event_type: str = "TicketCreatedEvent"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
    
    # Event Payload
    ticket_id: UUID
    company_id: UUID
    reference_code: str
    title: str
    ticket_type: str  # Enum value as string for better JSON portability
    priority: str
    module_origin: Optional[str] = None
    area: Optional[str] = None
    
    assigned_to_id: Optional[UUID] = None
    created_by_id: UUID
    
    # Optional metadata that might be useful for Notification Routing
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- Fase 6: Eventos de Estado y Notificación ---

class TicketStatusChangedEvent(BaseModel):
    """
    Dispatched when a ticket's status changes.
    The notification_service uses `recipient_id` to route the alert
    to the original reporter/creator of the ticket.
    """
    event_id: UUID = Field(default_factory=uuid.uuid4)
    event_type: str = "TicketStatusChangedEvent"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"

    ticket_id: UUID
    company_id: UUID
    reference_code: str
    title: str
    old_status: str
    new_status: str
    recipient_id: UUID           # A quién notificar (reported_by o created_by)
    changed_by_id: UUID          # Quién hizo el cambio
    area: Optional[str] = None
    module_origin: Optional[str] = None
    ticket_type: Optional[str] = None
    priority: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class TicketAutoClosedEvent(BaseModel):
    """
    Dispatched when a ticket is auto-closed by an external event
    (e.g., Kardex entry confirmed for MATERIAL_RECEIPT tickets).
    Notifies the original creator that the ticket was resolved automatically.
    """
    event_id: UUID = Field(default_factory=uuid.uuid4)
    event_type: str = "TicketAutoClosedEvent"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"

    ticket_id: UUID
    company_id: UUID
    reference_code: str
    title: str
    trigger_event: str           # e.g., "KARDEX_ENTRY_CONFIRMED"
    recipient_id: UUID           # Creador original a notificar
    source_service: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

