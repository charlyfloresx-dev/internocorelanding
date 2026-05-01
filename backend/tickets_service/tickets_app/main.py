from common.security.cors_setup import setup_cors
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from common.config import settings
from common.middleware import InternoCoreGlobalMiddleware
from tickets_app.routers import ticket_routes

app = FastAPI(
    title="Interno Tickets Service",
    version="1.0.0",
)

# CORS
setup_cors(app)

app.add_middleware(InternoCoreGlobalMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "tickets_service"}

# Include Routers
# Use the common api_v1_str if available, otherwise fallback to "/api/v1"
api_v1_prefix = getattr(settings, "int_api_v1_str", "/api/v1")
app.include_router(ticket_routes.router, prefix=api_v1_prefix)

if __name__ == "__main__":
    import uvicorn
    # Note: Port is usually handled by Docker mapping, but we keep the default for completeness
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
