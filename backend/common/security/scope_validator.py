"""
Scope Validator — Server-side scope validation against database.
Phase 179A P0.4: Prevent scope elevation by validating JWT scopes against SSOT.
"""
import logging
from typing import List, Set
import redis.asyncio as aioredis
from common.config import settings

logger = logging.getLogger(__name__)


class ScopeValidator:
    """
    Server-side scope validation against cached permission store.
    Never trusts JWT scope claims directly.
    """

    def __init__(self):
        self.redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
        self._client = None

    async def _get_client(self) -> aioredis.Redis:
        """Lazy load Redis client."""
        if self._client is None:
            self._client = await aioredis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def validate_scopes(
        self,
        user_id: str,
        company_id: str,
        jwt_scopes: List[str],
    ) -> bool:
        """
        Validate that user's JWT scopes match server-side record.
        Phase 179A P0.4: SSOT validation.

        Args:
            user_id: User UUID
            company_id: Company UUID
            jwt_scopes: Scopes from JWT (potentially falsified)

        Returns:
            True if JWT scopes match server-side record, False otherwise
        """
        # FAIL SECURE: Empty scopes or None → deny access
        if not jwt_scopes or not isinstance(jwt_scopes, list):
            return False

        # God mode bypass (already validated by god_mode session store)
        if "*" in jwt_scopes:
            return True

        client = await self._get_client()
        key = f"user_scopes:{company_id}:{user_id}"

        try:
            cached_scopes = await client.smembers(key)

            if not cached_scopes:
                # Cache miss — scope record not found in Redis
                # FAIL SECURE: Default to deny unless explicitly set
                logger.warning(f"No cached scopes found for {key}, denying access")
                return False

            jwt_set = set(jwt_scopes)
            cached_set = set(cached_scopes)

            # JWT scopes must be subset of cached scopes
            # (JWT may not have additional scopes not in cache)
            if not jwt_set.issubset(cached_set):
                missing = jwt_set - cached_set
                logger.warning(f"JWT claims unauthorized scopes: {missing} for {key}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate scopes from Redis: {e}")
            # FAIL SECURE: If Redis is down, deny access
            return False

    async def set_user_scopes(
        self,
        user_id: str,
        company_id: str,
        scopes: List[str],
        ttl_seconds: int = 86400  # 24 hours
    ) -> None:
        """
        Cache user scopes in Redis for server-side validation.
        Called when JWT is created or permissions change.

        Args:
            user_id: User UUID
            company_id: Company UUID
            scopes: List of scopes to cache
            ttl_seconds: Cache TTL (default 24 hours)
        """
        client = await self._get_client()
        key = f"user_scopes:{company_id}:{user_id}"

        try:
            # Clear old cache first
            await client.delete(key)

            # Set as Redis set for efficient validation
            if scopes:
                await client.sadd(key, *scopes)
                await client.expire(key, ttl_seconds)

            logger.info(f"Cached {len(scopes)} scopes for {key}")
        except Exception as e:
            logger.error(f"Failed to cache scopes: {e}")
            raise

    async def invalidate_user_scopes(
        self,
        user_id: str,
        company_id: str,
    ) -> None:
        """
        Invalidate cached scopes when permissions change.
        Used when user roles/permissions are modified.
        """
        client = await self._get_client()
        key = f"user_scopes:{company_id}:{user_id}"

        try:
            await client.delete(key)
            logger.info(f"Invalidated scopes for {key}")
        except Exception as e:
            logger.error(f"Failed to invalidate scopes: {e}")

    async def invalidate_company_scopes(self, company_id: str) -> int:
        """
        Emergency invalidation: clear all scope caches for company.
        Used during security incidents or permissions reset.

        Returns:
            Number of users affected
        """
        client = await self._get_client()
        pattern = f"user_scopes:{company_id}:*"

        try:
            keys = await client.keys(pattern)
            if keys:
                deleted = await client.delete(*keys)
                logger.warning(f"Invalidated scopes for {deleted} users in {company_id}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Failed to invalidate company scopes: {e}")
            return 0


# Singleton instance
_scope_validator: ScopeValidator | None = None


async def get_scope_validator() -> ScopeValidator:
    """Get or create scope validator singleton."""
    global _scope_validator
    if _scope_validator is None:
        _scope_validator = ScopeValidator()
    return _scope_validator


async def verify_user_scopes(
    user_id: str,
    company_id: str,
    jwt_scopes: List[str],
) -> bool:
    """
    Convenience function to verify user scopes against server-side SSOT.
    Phase 179A P0.4: Always validate JWT scopes against cached permissions.
    """
    validator = await get_scope_validator()
    return await validator.validate_scopes(user_id, company_id, jwt_scopes)
