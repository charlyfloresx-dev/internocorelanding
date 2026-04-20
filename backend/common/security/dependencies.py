from fastapi import Depends, HTTPException, status
from common.context import request_context
from common.security.auth_payload import TokenPayload

async def get_current_user() -> TokenPayload:
    """
    FastAPI Dependency to retrieve the current authenticated user from context.
    The context is populated by the AuthMiddleware.
    """
    context = request_context.get()
    if not context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid authentication credentials not found in request context",
        )
    return context

async def get_current_active_user(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Ensures the user is not readonly or in any state that prevents normal operation.
    """
    if current_user.readonly:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is in READ-ONLY mode. Mutation not allowed."
        )
    return current_user
