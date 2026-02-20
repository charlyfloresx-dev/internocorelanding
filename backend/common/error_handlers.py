from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import DomainException

async def domain_exception_handler(request: Request, exc: DomainException):
    """
    Global Exception Handler para capturar errores de dominio y
    transformarlos en el formato estándar ApiResponse.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "data": None,
            "meta": {
                "details": exc.details,
                "path": request.url.path
            }
        }
    )

# Nota: Registrar en main.py con app.add_exception_handler(DomainException, domain_exception_handler)