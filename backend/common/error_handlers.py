from fastapi import Request
from fastapi.responses import JSONResponse
from .exceptions import DomainException

async def domain_exception_handler(request: Request, exc: DomainException):
    """
    Global Exception Handler to capture domain errors and
    transform them into the standard ApiResponse format.
    """
    from .exceptions import UnauthorizedException, NotFoundException, ConflictException, BusinessRuleException
    
    # Industrial Mapping (Maturity Phase 37)
    status_code = getattr(exc, "status_code", 400)
    
    # Robust error_code mapping based on class name or explicit attribute
    error_code = getattr(exc, "code", None)
    if not error_code:
        if isinstance(exc, UnauthorizedException):
            error_code = "UNAUTHORIZED"
        elif isinstance(exc, NotFoundException):
            error_code = "NOT_FOUND"
        elif isinstance(exc, ConflictException):
            error_code = "CONFLICT"
        elif isinstance(exc, BusinessRuleException):
            error_code = "BUSINESS_RULE_VIOLATION"
        else:
            error_code = "DOMAIN_ERROR"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "code": error_code,
            "message": str(exc),
            "data": None,
            "meta": {
                "details": getattr(exc, "details", {}),
                "path": request.url.path,
                "type": type(exc).__name__
            }
        }
    )

# Note: Register in main.py with app.add_exception_handler(DomainException, domain_exception_handler)