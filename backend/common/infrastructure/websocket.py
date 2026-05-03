import json
import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        # active_connections: { company_id: [WebSocket, ...] }
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, company_id: str):
        await websocket.accept()
        if company_id not in self.active_connections:
            self.active_connections[company_id] = []
        self.active_connections[company_id].append(websocket)
        logger.info(f"🚀 WebSocket connected for company: {company_id}. Total: {len(self.active_connections[company_id])}")

    def disconnect(self, websocket: WebSocket, company_id: str):
        if company_id in self.active_connections:
            if websocket in self.active_connections[company_id]:
                self.active_connections[company_id].remove(websocket)
            if not self.active_connections[company_id]:
                del self.active_connections[company_id]
        logger.info(f"🛑 WebSocket disconnected for company: {company_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_company(self, company_id: str, message: Any):
        if company_id in self.active_connections:
            payload = json.dumps(message)
            for connection in self.active_connections[company_id]:
                try:
                    await connection.send_text(payload)
                except Exception as e:
                    logger.error(f"❌ Error broadcasting to {company_id}: {e}")
                    # We don't remove here to avoid mutating list during iteration, 
                    # disconnection is handled by the websocket loop

    async def broadcast_global(self, message: Any):
        payload = json.dumps(message)
        for company_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(payload)
                except Exception as e:
                    logger.error(f"❌ Error broadcasting global: {e}")

# Global Instance for the Monolith
manager = ConnectionManager()
