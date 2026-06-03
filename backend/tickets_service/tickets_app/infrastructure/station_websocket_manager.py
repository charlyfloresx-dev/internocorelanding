import json
import logging
from typing import Dict, List
from fastapi import WebSocket
from datetime import datetime, timezone

logger = logging.getLogger("station_websocket")

class StationWebSocketManager:
    """Manages WebSocket connections per MES resource (station_id)."""

    def __init__(self):
        # active_connections: { station_id: [WebSocket, ...] }
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, station_id: str):
        """Accept and register a WebSocket connection for a station."""
        await websocket.accept()
        if station_id not in self.active_connections:
            self.active_connections[station_id] = []
        self.active_connections[station_id].append(websocket)
        logger.info(f"🚀 Ticket realtime connected for station {station_id}. Total: {len(self.active_connections[station_id])}")

    def disconnect(self, websocket: WebSocket, station_id: str):
        """Unregister a WebSocket connection."""
        if station_id in self.active_connections:
            if websocket in self.active_connections[station_id]:
                self.active_connections[station_id].remove(websocket)
            if not self.active_connections[station_id]:
                del self.active_connections[station_id]
        logger.info(f"🛑 Ticket realtime disconnected for station {station_id}")

    async def broadcast_to_station(self, station_id: str, event: dict):
        """Broadcast a ticket event to all clients connected to a station."""
        if station_id not in self.active_connections:
            return

        payload = json.dumps(event)
        disconnected = []

        for connection in self.active_connections[station_id]:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"❌ Error broadcasting to station {station_id}: {e}")
                disconnected.append(connection)

        # Remove dead connections
        for connection in disconnected:
            if station_id in self.active_connections:
                try:
                    self.active_connections[station_id].remove(connection)
                except ValueError:
                    pass

        if station_id in self.active_connections and not self.active_connections[station_id]:
            del self.active_connections[station_id]

    async def emit_ticket_event(
        self,
        event_type: str,
        ticket_id: str,
        station_id: str,
        priority: str | None = None,
        status: str | None = None
    ):
        """Emit a ticket event to all clients connected to a station."""
        event = {
            "event_type": event_type,
            "ticket_id": ticket_id,
            "station_id": station_id,
            "priority": priority,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast_to_station(station_id, event)

# Global instance for tickets realtime
station_manager = StationWebSocketManager()
