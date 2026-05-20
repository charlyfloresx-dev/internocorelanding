from common.security.cors_setup import setup_cors
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware

app = FastAPI(
    title="Interno Notification Service",
    version="1.0.0",
)

# CORS
setup_cors(app)

app.add_middleware(InternoCoreGlobalMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notification_service"}

from app.routers import event_routes, notification_routes, whatsapp_routes
from app.core.websocket import manager
from fastapi import WebSocket, WebSocketDisconnect

app.include_router(event_routes.router, prefix="/api/v1")
app.include_router(notification_routes.router, prefix="/api/v1")
app.include_router(whatsapp_routes.router, prefix="/api/v1/whatsapp", tags=["WhatsApp Admin"])

@app.websocket("/ws/{company_id}")
async def websocket_endpoint(websocket: WebSocket, company_id: str):
    # In Phase 64, we simplify. In production, we should extract user_id from token
    # For now, we treat each connection as a company-level listener.
    user_id = "global_listener" 
    
    await manager.connect(websocket, company_id, user_id)
    try:
        while True:
            # Keep-alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id, user_id)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket, company_id, user_id)

if __name__ == "__main__":
    import uvicorn
    # Note: Port is usually handled by Docker mapping, but we keep the default for completeness
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
