from app.api.v1.endpoints import internal, admin

app = FastAPI(
    title="Interno Core - Subscription Service",
    description="Microservicio de Suscripciones, Entitlements y Licenciamiento",
    version="1.0.0"
)

# Rutas
app.include_router(internal.router, prefix="/internal", tags=["Internal"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "subscription_service"}
