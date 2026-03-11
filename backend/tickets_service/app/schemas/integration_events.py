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
