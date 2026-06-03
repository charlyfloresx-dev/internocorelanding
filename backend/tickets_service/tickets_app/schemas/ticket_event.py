from pydantic import BaseModel
from datetime import datetime

class TicketEvent(BaseModel):
    """WebSocket event payload for real-time ticket updates."""
    event_type: str  # "ticket.created" | "ticket.updated" | "ticket.assigned" | "ticket.status_changed"
    ticket_id: str
    station_id: str
    priority: str | None = None
    status: str | None = None
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "ticket.created",
                "ticket_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "station_id": "a47ac10b-58cc-4372-a567-0e02b2c3d479",
                "priority": "CRÍTICA",
                "status": "Nuevo",
                "timestamp": "2026-06-03T02:59:00Z"
            }
        }
