from functools import wraps
from typing import List, Union
from fastapi import Request
from common.exceptions import UnauthorizedException
from common.context import request_context

def requires_role(roles: Union[str, List[str]]):
    """
    FastAPI Decorator for Role-Based Access Control (RBAC).
    
    Validates that the current user context (populated by middleware)
    contains at least one of the required roles.
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Recuperar contexto de la petición
            context = request_context.get()
            
            if not context:
                raise UnauthorizedException(message="Authentication context missing")

            # 2. Validar rol principal o lista de roles extendida (Case Insensitive)
            user_roles = {r.upper() for r in context.role_names}
            if context.role:
                user_roles.add(context.role.upper())

            required_roles = [r.upper() for r in roles]

            # Check intersection
            if not any(role in user_roles for role in required_roles):
                raise UnauthorizedException(
                    message=f"Access denied. Required roles: {roles}. Your roles: {list(user_roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
