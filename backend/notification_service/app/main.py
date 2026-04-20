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

from app.routers import event_routes
app.include_router(event_routes.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    # Note: Port is usually handled by Docker mapping, but we keep the default for completeness
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
