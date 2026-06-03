"""
Session Store Client for Redis-backed security verification.
Phase 179A P0.3: god_mode verification against server-side session store.
"""
import json
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
import redis.asyncio as aioredis
from common.config import settings

logger = logging.getLogger(__name__)


class SessionStoreClient:
    """
    Redis-backed session store for security-critical claims.
    Prevents token falsification by maintaining server-side source of truth.
    """

    def __init__(self):
        self.redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
        self._client = None

    async def _get_client(self) -> aioredis.Redis:
        """Lazy load Redis client."""
        if self._client is None:
            self._client = await aioredis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def set_god_mode(
        self,
        user_id: str,
        company_id: str,
        enabled: bool,
        ttl_seconds: int = 3600
    ) -> None:
        """
        Set god_mode status for user in company (server-side source of truth).

        Args:
            user_id: User UUID
            company_id: Company UUID
            enabled: Whether god_mode is active
            ttl_seconds: Time-to-live for this setting (default 1 hour)
        """
        client = await self._get_client()
        key = f"god_mode:{company_id}:{user_id}"
        value = json.dumps({
            "enabled": enabled,
            "set_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        })

        try:
            await client.setex(key, ttl_seconds, value)
            logger.info(f"god_mode status set: {key} = {enabled}")
        except Exception as e:
            logger.error(f"Failed to set god_mode in Redis: {e}")
            raise

    async def get_god_mode(self, user_id: str, company_id: str) -> bool:
        """
        Verify god_mode status from server-side session store.
        Returns False if key doesn't exist (default: no god_mode access).

        Args:
            user_id: User UUID
            company_id: Company UUID

        Returns:
            True if god_mode is enabled and not expired, False otherwise
        """
        client = await self._get_client()
        key = f"god_mode:{company_id}:{user_id}"

        try:
            value = await client.get(key)
            if not value:
                return False  # Key doesn't exist = god_mode disabled

            data = json.loads(value)
            enabled = data.get("enabled", False)

            # Verify expiration
            expires_at = datetime.fromisoformat(data.get("expires_at", ""))
            if datetime.now(timezone.utc) > expires_at:
                await client.delete(key)
                logger.warning(f"god_mode session expired: {key}")
                return False

            return enabled

        except json.JSONDecodeError:
            logger.error(f"Corrupted god_mode session data: {key}")
            await client.delete(key)
            return False
        except Exception as e:
            logger.error(f"Failed to verify god_mode from Redis: {e}")
            # FAIL SECURE: If Redis is down, deny god_mode
            return False

    async def revoke_god_mode(self, user_id: str, company_id: str) -> None:
        """Immediately revoke god_mode access for user."""
        client = await self._get_client()
        key = f"god_mode:{company_id}:{user_id}"

        try:
            await client.delete(key)
            logger.info(f"god_mode revoked: {key}")
        except Exception as e:
            logger.error(f"Failed to revoke god_mode: {e}")
            raise

    async def revoke_all_god_mode_for_company(self, company_id: str) -> int:
        """
        Emergency revocation: remove all god_mode sessions for a company.
        Used when security breach detected.

        Returns:
            Number of sessions revoked
        """
        client = await self._get_client()
        pattern = f"god_mode:{company_id}:*"

        try:
            keys = await client.keys(pattern)
            if keys:
                deleted = await client.delete(*keys)
                logger.warning(f"Emergency god_mode revocation: {deleted} sessions revoked for {company_id}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Failed to revoke all god_mode sessions: {e}")
            return 0


# Singleton instance
_session_store: Optional[SessionStoreClient] = None


async def get_session_store() -> SessionStoreClient:
    """Get or create session store singleton."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStoreClient()
    return _session_store


async def verify_god_mode(user_id: str, company_id: str) -> bool:
    """
    Convenience function to verify god_mode status against server-side store.
    Phase 179A P0.3: Always verify against Redis, never trust JWT claim alone.
    """
    session_store = await get_session_store()
    return await session_store.get_god_mode(user_id, company_id)
