from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import DomainException

async def domain_exception_handler(request: Request, exc: DomainException):
    """
    Global Exception Handler to capture domain errors and
    transform them into the standard ApiResponse format.
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

# Note: Register in main.py with app.add_exception_handler(DomainException, domain_exception_handler)