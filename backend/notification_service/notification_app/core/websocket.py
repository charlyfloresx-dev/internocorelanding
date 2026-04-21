import logging
import json
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Estructura: { company_id: { user_id: [WebSocket, ...] } }
        self.active_connections: Dict[str, Dict[str, List[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, company_id: str, user_id: str):
        await websocket.accept()
        
        if company_id not in self.active_connections:
            self.active_connections[company_id] = {}
        
        if user_id not in self.active_connections[company_id]:
            self.active_connections[company_id][user_id] = []
            
        self.active_connections[company_id][user_id].append(websocket)
        logger.info(f"🚀 WebSocket Connected: User {user_id} in Company {company_id}")

    def disconnect(self, websocket: WebSocket, company_id: str, user_id: str):
        if company_id in self.active_connections:
            if user_id in self.active_connections[company_id]:
                if websocket in self.active_connections[company_id][user_id]:
                    self.active_connections[company_id][user_id].remove(websocket)
                
                if not self.active_connections[company_id][user_id]:
                    del self.active_connections[company_id][user_id]
            
            if not self.active_connections[company_id]:
                del self.active_connections[company_id]
        
        logger.info(f"🔌 WebSocket Disconnected: User {user_id}")

    async def send_personal_message(self, message: dict, user_id: str, company_id: str):
        """Envía un mensaje a todas las sesiones activas de un usuario específico."""
        if company_id in self.active_connections:
            if user_id in self.active_connections[company_id]:
                for connection in self.active_connections[company_id][user_id]:
                    await connection.send_text(json.dumps(message))

    async def broadcast_to_company(self, message: dict, company_id: str):
        """Envía un mensaje a TODOS los usuarios conectados de una empresa."""
        if company_id in self.active_connections:
            for user_id in self.active_connections[company_id]:
                for connection in self.active_connections[company_id][user_id]:
                    try:
                        await connection.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"❌ Error broadcasting to {user_id}: {e}")

# Instancia global para ser usada por los servicios
manager = ConnectionManager()
