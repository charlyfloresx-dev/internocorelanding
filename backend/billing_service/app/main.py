import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user_payload
from app.api.v1.endpoints import invoices, payments
from common.exceptions import DomainException

app = FastAPI(
    title="Billing Service",
    version="1.0.0",
    description="Microservicio de Facturación, Notas de Crédito y Pagos - InternoCore",
)

# 1. CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Handler de errores de dominio
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": exc.message},
    )

# 3. Rutas protegidas (todas requieren token multitenant)
app.include_router(
    invoices.router,
    prefix="/api/v1/invoices",
    tags=["Invoices"],
    dependencies=[Depends(get_current_user_payload)],
)

app.include_router(
    payments.router,
    prefix="/api/v1/payments",
    tags=["Payments"],
    dependencies=[Depends(get_current_user_payload)],
)

# 4. Health check
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "service": "billing_service",
        "version": "1.0.0",
    }
