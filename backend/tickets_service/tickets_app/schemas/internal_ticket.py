from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Any
from tickets_app.core.constants import TicketPriority, TicketType

class InternalTicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=10)
    priority: TicketPriority = TicketPriority.MEDIUM
    ticket_type: TicketType = TicketType.SUPPORT
    source_service: str = Field(..., description="Service that triggered the internal ticket")
    
    # Context for SSOT and Debouncing
    product_id: Optional[UUID] = Field(None, description="Context: Product UUID")
    warehouse_id: Optional[UUID] = Field(None, description="Context: Warehouse UUID")
    transaction_id: Optional[UUID] = Field(None, description="Traceability UUID")
    deep_link_id: Optional[UUID] = Field(None, description="Deep link reference for the UI")
    
    # --- Fase 5: Campos Operacionales ---
    station_id: Optional[UUID] = Field(None, description="MES Station UUID (required for MAINTENANCE)")
    parent_ticket_id: Optional[UUID] = Field(None, description="Parent ticket for ESCALATION/DOWNTIME")
    area: Optional[str] = Field(None, description="Área operacional: Producción, Almacén, Mantenimiento")
    
    metadata: Optional[dict] = Field(None, description="Additional context freeform dictionary")

class InternalTicketResolve(BaseModel):
    ticket_id: UUID
    trigger_event: str = Field(..., description="Event that caused auto-closure, e.g. KARDEX_ENTRY_CONFIRMED")
    source_service: str = Field(..., description="Service emitting the resolution")
    resolution_notes: str = Field(..., description="Notes regarding the automatic resolution")
