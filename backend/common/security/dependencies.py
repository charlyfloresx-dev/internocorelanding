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

from fastapi import Request

async def get_current_active_user(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    Ensures the user is not readonly or in any state that prevents normal operation.
    """
    if current_user.readonly and request.method not in ("GET", "OPTIONS", "HEAD"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is in READ-ONLY mode. Mutation not allowed."
        )
        
    # --- PHASE 2 HEARTBEAT: REDIS BLOCKLIST & STATUS CHECK ---
    now = time.time()
    cache_key = f"user_status:{current_user.sub}"
    
    # Check local cache first (solo aplica a sesiones normales, no god mode)
    if not current_user.god_mode and cache_key in _user_status_cache and _user_status_cache[cache_key] > now:
        return current_user

    try:
        r = get_redis()

        # Sesión GOD MODE: verificar que el JTI no fue revocado en Redis
        if current_user.god_mode and current_user.jti:
            jti_valid = await r.get(f"godmode:{current_user.jti}")
            if not jti_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "ERR_GOD_MODE_EXPIRED", "message": "La sesión de emergencia ha expirado o fue revocada."},
                )
            return current_user

        # Sesión normal: verificar blocklist de usuario
        is_inactive = await r.get(f"blacklist:{current_user.sub}")
        if is_inactive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account has been deactivated or token revoked."
            )
        _user_status_cache[cache_key] = now + _CACHE_TTL
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not reach Redis for heartbeat: {e}")

    return current_user

def _scope_satisfies(user_scopes: set[str], required_scope: str) -> bool:
    """
    Check if any user scope satisfies a required scope.

    Supports three matching modes:
      1. Exact match:     user has "master_data.product.read" and required is "master_data.product.read"
      2. Wildcard:        user has "*" → satisfies everything
      3. Namespace match: required is coarse "master_data:read" (colon-separated),
                          satisfied by any granular user scope like "master_data.product.read".
                          The "manage" suffix satisfies both :read and :write.
    """
    if "*" in user_scopes:
        return True
    if required_scope in user_scopes:
        return True

    # Namespace matching for coarse scopes (e.g. "master_data:read")
    if ":" in required_scope:
        namespace, action = required_scope.split(":", 1)
        for us in user_scopes:
            if not us.startswith(namespace + "."):
                continue
            # e.g. user has "master_data.product.read", required is "master_data:read"
            slug_suffix = us.rsplit(".", 1)[-1]  # "read", "write", "manage", etc.
            if slug_suffix == action:
                return True
            # "manage" implies both read and write
            if slug_suffix == "manage" and action in ("read", "write"):
                return True
        return False

    return False


def require_scope(required_scopes: list[str]):
    """
    Dependency factory to enforce scope-based access control.
    Supports both exact granular slugs ("master_data.product.read") and
    coarse namespace scopes ("master_data:read") which match any granular
    slug in that namespace.

    Example: @router.get("/", dependencies=[Security(require_scope(["master_data:read"]))])
    """
    async def _require_scope(
        current_user: TokenPayload = Depends(get_current_active_user)
    ):
        # Admin / God Mode Bypass
        if "GOD_MODE_ADMIN" in (current_user.role_names or []) or "*" in (current_user.scopes or []):
            return current_user

        user_scopes = set(current_user.scopes or [])

        missing = [
            rs for rs in required_scopes
            if not _scope_satisfies(user_scopes, rs)
        ]

        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing scopes: {missing}"
            )
        return current_user

    return _require_scope
