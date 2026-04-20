from functools import wraps
from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)

def idempotent():
    """
    Decorator to extract the X-Client-Request-ID from the Request headers
    and inject it into the route handler's kwargs. The handler must inject this key 
    into the Repository's commit cycle to guarantee atomic idempotency 
    within the same database transaction.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                # Fallback: try to find the Request object in kwargs or args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                if not request:
                    for arg in kwargs.values():
                        if isinstance(arg, Request):
                            request = arg
                            break

            if request:
                client_request_id = request.headers.get("X-Client-Request-ID")
                if not client_request_id:
                    raise HTTPException(
                        status_code=400, 
                        detail="Missing X-Client-Request-ID header required for idempotent operations."
                    )
                kwargs["client_request_id"] = client_request_id
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
