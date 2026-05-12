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

import redis.asyncio as redis
from common.config import settings
import time

# Simple in-memory cache to avoid hitting Redis for every single request (5 min TTL)
# Format: {"user:sub": expiration_timestamp}
_user_status_cache = {}
_CACHE_TTL = 300  # 5 minutes

# Lazy redis client
_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL if settings.REDIS_URL else "redis://localhost:6379", decode_responses=True)
    return _redis_client

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
        
    # --- PHASE 2 HEARTBEAT: REDIS BLOCKLIST & STATUS CHECK ---
    now = time.time()
    cache_key = f"user_status:{current_user.sub}"
    
    # Check local cache first
    if cache_key in _user_status_cache and _user_status_cache[cache_key] > now:
        return current_user # Still valid in local cache
        
    # Not in cache or expired, check Redis
    try:
        r = get_redis()
        # Check if JWT ID (jti) is blacklisted (if jti exists in token)
        # Note: current_user is a TokenPayload, we could check jti if we add it to the model.
        # Check if user is inactive
        is_inactive = await r.get(f"blacklist:{current_user.sub}")
        if is_inactive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account has been deactivated or token revoked."
            )
        # Cache the valid status locally for 5 minutes
        _user_status_cache[cache_key] = now + _CACHE_TTL
    except Exception as e:
        # Fail-open strategy if Redis is unreachable (similar to Rate Limiter)
        import logging
        logging.getLogger(__name__).warning(f"Could not reach Redis for heartbeat: {e}")

    return current_user

def require_scope(required_scopes: list[str]):
    """
    Dependency factory to enforce scope-based access control.
    Example: @router.post("/", dependencies=[Depends(require_scope(["inv:write"]))])
    """
    async def _require_scope(
        current_user: TokenPayload = Depends(get_current_active_user)
    ):
        # Admin / God Mode Bypass
        if "GOD_MODE_ADMIN" in current_user.role_names or "*" in current_user.scopes:
            return current_user
            
        user_scopes = set(current_user.scopes)
        required = set(required_scopes)
        
        # Check if the user has AT LEAST ONE of the required scopes, or require all?
        # Usually requires all if passed as a list, or we can just do intersection if it's an 'ANY' check.
        # Let's enforce that the user must have ALL the required scopes.
        if not required.issubset(user_scopes):
            missing = required - user_scopes
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing scopes: {list(missing)}"
            )
        return current_user

    return _require_scope
